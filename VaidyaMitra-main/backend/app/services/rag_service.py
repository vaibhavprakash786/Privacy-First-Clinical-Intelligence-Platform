"""
RAG Service — Retrieval Augmented Generation

Embedding generation and vector retrieval for grounded AI responses.
Used to prevent hallucination by injecting relevant context.
Integrated with AWS DynamoDB caching for embedding persistence.
"""

import json
import logging
import uuid
import hashlib
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.dynamodb_client import get_dynamodb_client, TABLE_RAG_EMBEDDINGS
from app.core.cache_client import CacheClient, get_cache_client

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service.
    
    Stores document embeddings and retrieves relevant context
    for grounding AI responses.
    """

    def __init__(self):
        self.db = get_dynamodb_client()
        self._embedding_cache: Dict[str, List[float]] = {}
        self.cache = get_cache_client()
        logger.info("RAG Service initialized with DynamoDB cache")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.
        Checks in-memory cache, then DynamoDB cache, then generates."""
        # L1: In-memory cache check
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]

        # L2: DynamoDB cache check
        cache_key = CacheClient.generate_cache_key("embedding", text_hash)
        cached = self.cache.get(cache_key)
        if cached is not None:
            embedding = cached.get("embedding", [])
            self._embedding_cache[text_hash] = embedding  # Promote to L1
            logger.info(f"Embedding CACHE HIT (DynamoDB) for text hash: {text_hash[:8]}")
            return embedding

        if settings.AI_MODE == "bedrock":
            try:
                import boto3
                client = boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)
                response = client.invoke_model(
                    modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
                    body=json.dumps({"inputText": text[:8000]}),
                    contentType="application/json",
                    accept="application/json",
                )
                body = json.loads(response["body"].read())
                embedding = body.get("embedding", [])
                self._embedding_cache[text_hash] = embedding
                # Persist to DynamoDB cache
                self.cache.put(
                    cache_key, {"embedding": embedding},
                    ttl_hours=settings.CACHE_TTL_EMBEDDING_HOURS,
                    service="embedding",
                    query_text=text[:100],
                )
                return embedding
            except Exception as e:
                logger.warning(f"Bedrock embedding failed, using mock: {e}")

        # Mock embedding — simple hash-based vector for dev
        embedding = self._mock_embedding(text)
        self._embedding_cache[text_hash] = embedding
        return embedding

    def _mock_embedding(self, text: str, dim: int = 256) -> List[float]:
        """Generate a deterministic mock embedding for development."""
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Expand hash to fill dimension
        values = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            values.append((hash_bytes[byte_idx] - 128) / 128.0)
        return values

    def store_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_type: str = "clinical",
    ) -> str:
        """Store a document with its embedding."""
        doc_id = str(uuid.uuid4())
        embedding = self.generate_embedding(content)

        item = {
            "doc_id": doc_id,
            "content": content[:5000],
            "doc_type": doc_type,
            "metadata": json.dumps(metadata),
            "embedding_dim": len(embedding),
            # Store first 50 dimensions for DynamoDB (full vectors go to dedicated vector store in production)
            "embedding_sample": embedding[:50],
        }

        self.db.put_item(TABLE_RAG_EMBEDDINGS, item)
        logger.info(f"Stored RAG document: {doc_id} (type={doc_type})")
        return doc_id

    def retrieve_context(
        self,
        query: str,
        doc_type: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        # In production, use vector similarity search (OpenSearch/pgvector)
        # For now, scan and do basic text matching
        try:
            items = self.db.scan_items(TABLE_RAG_EMBEDDINGS, limit=100)

            # Simple text relevance scoring
            query_terms = set(query.lower().split())
            scored = []
            for item in items:
                if doc_type and item.get("doc_type") != doc_type:
                    continue
                content = item.get("content", "").lower()
                score = sum(1 for term in query_terms if term in content)
                if score > 0:
                    scored.append((score, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:top_k]]

        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    def build_grounded_prompt(
        self,
        base_prompt: str,
        query: str,
        doc_type: Optional[str] = None,
    ) -> str:
        """Build a prompt with RAG context injected."""
        relevant_docs = self.retrieve_context(query, doc_type=doc_type)

        if not relevant_docs:
            return base_prompt

        context_parts = []
        for doc in relevant_docs:
            content = doc.get("content", "")
            context_parts.append(content)

        rag_context = "\n---\n".join(context_parts)
        grounded_prompt = f"""Use the following relevant context to ground your response:

CONTEXT:
{rag_context}

---

{base_prompt}

IMPORTANT: Base your response on the provided context. If the context doesn't contain enough information, say so clearly."""

        return grounded_prompt


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
