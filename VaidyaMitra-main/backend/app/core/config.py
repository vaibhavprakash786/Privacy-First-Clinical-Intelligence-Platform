"""
Application configuration using Pydantic settings.
All settings loaded from environment variables or .env file.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # --- AWS Configuration ---
    AWS_REGION: str = Field(default="ap-south-1")
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_SESSION_TOKEN: str = Field(
        default="",
        description="Optional STS session token for temporary credentials.",
    )

    # DynamoDB
    DYNAMODB_ENDPOINT_URL: str = Field(
        default="",
        description="Local DynamoDB endpoint (e.g. http://localhost:8001). Leave empty for AWS.",
    )
    DYNAMODB_TABLE_PREFIX: str = Field(default="vaidyamitra_")

    # S3
    S3_BUCKET_NAME: str = Field(default="vaidyamitra-data")
    S3_ENDPOINT_URL: str = Field(default="")

    # Bedrock
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-haiku-20240307-v1:0")
    BEDROCK_EMBEDDING_MODEL_ID: str = Field(default="amazon.titan-embed-text-v2:0")
    BEDROCK_REGION: str = Field(default="us-east-1")

    # --- API Configuration ---
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_RELOAD: bool = Field(default=True)
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3001")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # --- Security ---
    API_KEY_HEADER: str = Field(default="X-API-Key")
    API_KEYS: str = Field(default="dev_key_12345")
    SECRET_KEY: str = Field(default="vaidyamitra-dev-secret-change-in-production")

    @property
    def api_keys_list(self) -> List[str]:
        return [key.strip() for key in self.API_KEYS.split(",")]

    # --- Privacy Layer ---
    PRESIDIO_CONFIDENCE_THRESHOLD: float = Field(default=0.5)
    PRIVACY_LAYER_TIMEOUT: int = Field(default=100)

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=10)

    # --- Logging ---
    LOG_LEVEL: str = Field(default="INFO")

    # --- AI Mode ---
    AI_MODE: str = Field(
        default="auto",
        description="'auto' = bedrock if credentials present else mock, 'bedrock' = force AWS, 'mock' = force mock",
    )

    # --- Cache Configuration ---
    CACHE_ENABLED: bool = Field(default=True, description="Enable/disable DynamoDB-backed AI result caching")
    CACHE_TTL_MEDICINE_HOURS: int = Field(default=168, description="Cache TTL for medicine identification (7 days)")
    CACHE_TTL_JANAUSHADHI_HOURS: int = Field(default=168, description="Cache TTL for Jan Aushadhi alternatives (7 days)")
    CACHE_TTL_DISEASE_HOURS: int = Field(default=24, description="Cache TTL for disease predictions (1 day)")
    CACHE_TTL_REPORT_HOURS: int = Field(default=72, description="Cache TTL for report simplification (3 days)")
    CACHE_TTL_QUERY_HOURS: int = Field(default=12, description="Cache TTL for orchestrator AI queries (12 hours)")
    CACHE_TTL_EMBEDDING_HOURS: int = Field(default=720, description="Cache TTL for RAG embeddings (30 days)")
    CACHE_MAX_MEMORY_ITEMS: int = Field(default=500, description="Max entries in in-memory LRU cache")

    @property
    def effective_ai_mode(self) -> str:
        """Resolve 'auto' mode: use bedrock if AWS credentials are present, else mock."""
        if self.AI_MODE == "auto":
            if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
                return "bedrock"
            return "mock"
        return self.AI_MODE

    @property
    def has_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)


# Global settings instance
settings = Settings()
