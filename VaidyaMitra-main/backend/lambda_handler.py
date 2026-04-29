"""
AWS Lambda Adapter for VaidyaMitra

Allows the FastAPI application to run serverless on AWS Lambda
using API Gateway or Function URLs.
"""

from mangum import Mangum
from app.main import app
import logging

# Ensure startup events run (DynamoDB/S3 verification)
handler = Mangum(app, lifespan="on")

logging.getLogger("mangum").setLevel(logging.INFO)
