"""
VaidyaMitra FastAPI Application Entry Point

Privacy-preserving clinical intelligence system
with AI-powered analysis for Bharat.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.middleware.error_handler import error_handler_middleware
from app.middleware.audit_logger import AuditLoggerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

# Configure structured logging (CloudWatch-ready)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("VaidyaMitra starting up...")

    try:
        from app.core.dynamodb_client import get_dynamodb_client
        db = get_dynamodb_client()
        db.ensure_tables()
        logger.info("DynamoDB tables verified")
    except Exception as e:
        logger.warning(f"DynamoDB setup skipped (will retry on first request): {e}")

    try:
        from app.core.s3_client import get_s3_client
        s3 = get_s3_client()
        s3.ensure_bucket()
        logger.info(f"S3 bucket '{settings.S3_BUCKET_NAME}' verified")
    except Exception as e:
        logger.warning(f"S3 setup skipped (will retry on first request): {e}")

    logger.info(f"AI Mode configured as: '{settings.AI_MODE}' -> effective mode: '{settings.effective_ai_mode}'")
    
    if settings.effective_ai_mode == "bedrock":
        logger.info(f"AWS Bedrock connected (model: {settings.BEDROCK_MODEL_ID})")
    else:
        logger.warning("AWS credentials missing or invalid. Bedrock AI falls back to local MOCK mode.")

    logger.info("VaidyaMitra API ready!")

    yield  # Application runs here

    # Shutdown
    logger.info("VaidyaMitra shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VaidyaMitra API",
    description=(
        "Privacy-preserving clinical intelligence system with AI-powered analysis. "
        "Built for Bharat with Jan Aushadhi generic medicine integration."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware
cors_origins = settings.cors_origins_list if settings.cors_origins_list else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# Rate limiting middleware
app.add_middleware(RateLimiterMiddleware)

# Audit logging middleware
app.add_middleware(AuditLoggerMiddleware)

# Global error handlers
error_handler_middleware(app)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "VaidyaMitra",
        "tagline": "Privacy-First Clinical Intelligence for Bharat",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs",
        "features": [
            "Clinical Summarization (AI)",
            "Change Detection",
            "Disease Prediction (Medicure ML)",
            "Jan Aushadhi Generic Medicine Search",
            "Privacy-First PII/PHI Masking",
            "Agentic AI Orchestration",
            "RAG-Grounded Responses",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
