"""
AWS DynamoDB-Backed Cache Client

Centralized caching layer for all VaidyaMitra AI services.
Uses DynamoDB with TTL for automatic expiration, plus an in-memory
LRU layer for ultra-fast repeated lookups within the same process.

Cacheable services:
  - medicine_id   : Medicine identification
  - janaushadhi   : Jan Aushadhi generic alternatives
  - disease       : Disease prediction
  - simplify      : Report simplification
  - summarize     : Report summarization
  - query         : Orchestrator AI queries
  - embedding     : RAG embeddings
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# DynamoDB cache table name
TABLE_AI_CACHE = f"{settings.DYNAMODB_TABLE_PREFIX}ai_cache"


class CacheClient:
    """
    DynamoDB-backed cache with in-memory LRU for hot entries.

    Flow:
    1. Check in-memory LRU → instant hit
    2. Check DynamoDB → network hit (fast, ~5ms single-digit ms reads)
    3. Miss → caller performs AI invocation → stores result via put()
    """

    def __init__(self):
        self._memory_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_memory = settings.CACHE_MAX_MEMORY_ITEMS
        self._stats = {"hits_memory": 0, "hits_dynamo": 0, "misses": 0, "stores": 0}
        self._db = None
        logger.info(
            f"CacheClient initialized (enabled={settings.CACHE_ENABLED}, "
            f"memory_max={self._max_memory})"
        )

    @property
    def db(self):
        """Lazy-load DynamoDB client to avoid circular imports."""
        if self._db is None:
            from app.core.dynamodb_client import get_dynamodb_client
            self._db = get_dynamodb_client()
        return self._db

    # ── Key Generation ─────────────────────────────────────────────

    @staticmethod
    def generate_cache_key(service: str, *parts: Any) -> str:
        """
        Generate a deterministic SHA-256 cache key.

        Args:
            service: Service identifier (e.g. 'medicine_id', 'janaushadhi')
            *parts: Variable arguments that form the cache identity
                    (query text, sorted symptoms, etc.)
        """
        raw = f"{service}:" + "|".join(str(p) for p in parts if p)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ── Read ───────────────────────────────────────────────────────

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result by key.

        Returns the cached data dict, or None on miss/expired.
        """
        if not settings.CACHE_ENABLED:
            return None

        # 1. Check in-memory LRU
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if entry.get("expires_at", 0) > time.time():
                self._memory_cache.move_to_end(cache_key)
                self._stats["hits_memory"] += 1
                logger.debug(f"Cache HIT (memory): {cache_key[:16]}...")
                return entry.get("data")
            else:
                # Expired in memory
                del self._memory_cache[cache_key]

        # 2. Check DynamoDB
        try:
            item = self.db.get_item(TABLE_AI_CACHE, {"cache_key": cache_key})
            if item is None:
                self._stats["misses"] += 1
                return None

            expires_at = item.get("expires_at", 0)
            if isinstance(expires_at, (int, float)) and expires_at <= time.time():
                # Expired (DynamoDB TTL hasn't cleaned it up yet)
                self._stats["misses"] += 1
                return None

            # Parse stored data
            data_str = item.get("data", "{}")
            data = json.loads(data_str) if isinstance(data_str, str) else data_str

            # Promote to in-memory cache
            self._memory_put(cache_key, data, expires_at)

            # Update hit count in DynamoDB (fire-and-forget)
            self._increment_hit_count(cache_key)

            self._stats["hits_dynamo"] += 1
            logger.debug(f"Cache HIT (dynamo): {cache_key[:16]}...")
            return data

        except Exception as e:
            logger.warning(f"Cache GET failed for {cache_key[:16]}: {e}")
            self._stats["misses"] += 1
            return None

    # ── Write ──────────────────────────────────────────────────────

    def put(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl_hours: int,
        service: str = "unknown",
        query_text: str = "",
    ) -> bool:
        """
        Store a result in cache.

        Args:
            cache_key: The hash key from generate_cache_key()
            data: The AI result dict to cache
            ttl_hours: Hours until expiry
            service: Service identifier for analytics
            query_text: Original query text (for debugging/analytics)
        """
        if not settings.CACHE_ENABLED:
            return False

        expires_at = int(time.time()) + (ttl_hours * 3600)

        try:
            item = {
                "cache_key": cache_key,
                "data": json.dumps(data, default=str),
                "service": service,
                "query_text": query_text[:200],  # Truncate for storage
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at,
                "hit_count": 0,
            }
            self.db.put_item(TABLE_AI_CACHE, item)

            # Also store in memory
            self._memory_put(cache_key, data, expires_at)

            self._stats["stores"] += 1
            logger.info(
                f"Cache STORE: {service} → {cache_key[:16]}... "
                f"(TTL={ttl_hours}h, query='{query_text[:50]}')"
            )
            return True

        except Exception as e:
            logger.warning(f"Cache PUT failed for {cache_key[:16]}: {e}")
            return False

    # ── Memory LRU ─────────────────────────────────────────────────

    def _memory_put(self, cache_key: str, data: Dict[str, Any], expires_at: float):
        """Add entry to in-memory LRU cache, evicting oldest if at capacity."""
        if cache_key in self._memory_cache:
            self._memory_cache.move_to_end(cache_key)
        self._memory_cache[cache_key] = {"data": data, "expires_at": expires_at}

        # Evict oldest entries if over capacity
        while len(self._memory_cache) > self._max_memory:
            self._memory_cache.popitem(last=False)

    # ── Analytics ──────────────────────────────────────────────────

    def _increment_hit_count(self, cache_key: str):
        """Increment the hit count for a cached entry (best-effort)."""
        try:
            table = self.db.dynamodb.Table(TABLE_AI_CACHE)
            table.update_item(
                Key={"cache_key": cache_key},
                UpdateExpression="SET hit_count = if_not_exists(hit_count, :zero) + :inc",
                ExpressionAttributeValues={":inc": 1, ":zero": 0},
            )
        except Exception:
            pass  # Non-critical, ignore failures

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics and most frequently queried items."""
        stats = {
            **self._stats,
            "total_requests": (
                self._stats["hits_memory"]
                + self._stats["hits_dynamo"]
                + self._stats["misses"]
            ),
            "hit_rate": 0.0,
            "memory_entries": len(self._memory_cache),
            "enabled": settings.CACHE_ENABLED,
        }

        total = stats["total_requests"]
        if total > 0:
            stats["hit_rate"] = round(
                (self._stats["hits_memory"] + self._stats["hits_dynamo"]) / total * 100,
                1,
            )

        # Fetch most popular cached items from DynamoDB
        try:
            items = self.db.scan_items(TABLE_AI_CACHE, limit=200)
            by_service: Dict[str, int] = {}
            top_queries: List[Dict] = []

            for item in items:
                svc = item.get("service", "unknown")
                by_service[svc] = by_service.get(svc, 0) + 1
                hit_count = item.get("hit_count", 0)
                if hit_count > 0:
                    top_queries.append({
                        "query": item.get("query_text", ""),
                        "service": svc,
                        "hits": hit_count,
                    })

            top_queries.sort(key=lambda x: x["hits"], reverse=True)
            stats["entries_by_service"] = by_service
            stats["total_dynamo_entries"] = len(items)
            stats["most_frequent_queries"] = top_queries[:10]

        except Exception as e:
            logger.warning(f"Failed to fetch cache analytics: {e}")
            stats["entries_by_service"] = {}
            stats["total_dynamo_entries"] = "unavailable"
            stats["most_frequent_queries"] = []

        return stats

    def clear(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cache entries.

        Args:
            service: If provided, only clear entries for this service.
                     If None, clear all entries.
        """
        cleared = 0

        # Clear memory cache
        if service:
            keys_to_remove = []
            # We can't filter memory by service (no metadata stored there),
            # so clear all memory on targeted clears too
            self._memory_cache.clear()
        else:
            self._memory_cache.clear()

        # Clear DynamoDB entries
        try:
            items = self.db.scan_items(TABLE_AI_CACHE, limit=500)
            for item in items:
                if service and item.get("service") != service:
                    continue
                self.db.delete_item(TABLE_AI_CACHE, {"cache_key": item["cache_key"]})
                cleared += 1
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

        # Reset stats
        self._stats = {"hits_memory": 0, "hits_dynamo": 0, "misses": 0, "stores": 0}

        logger.info(f"Cache cleared: {cleared} entries (service={service or 'all'})")
        return {"cleared": cleared, "service": service or "all"}


# ── Singleton ─────────────────────────────────────────────────────

_cache_client: Optional[CacheClient] = None


def get_cache_client() -> CacheClient:
    """Get or create the singleton CacheClient."""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
