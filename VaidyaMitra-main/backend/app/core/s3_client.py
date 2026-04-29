"""
S3 Client

AWS S3 operations for PDF storage, model artifacts, and embedding backups.
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for file storage operations."""

    def __init__(self):
        kwargs = {"region_name": settings.AWS_REGION}
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        if settings.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.s3 = boto3.client("s3", **kwargs)
        self.bucket_name = settings.S3_BUCKET_NAME
        logger.info(f"S3 client initialized (bucket: {self.bucket_name})")

    def ensure_bucket(self):
        """Create the S3 bucket if it doesn't exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                create_params = {"Bucket": self.bucket_name}
                if settings.AWS_REGION != "us-east-1":
                    create_params["CreateBucketConfiguration"] = {
                        "LocationConstraint": settings.AWS_REGION
                    }
                self.s3.create_bucket(**create_params)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")

    def upload_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to S3."""
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.info(f"Uploaded to S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return False

    def download_file(self, key: str) -> Optional[bytes]:
        """Download a file from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            return None

    def get_presigned_url(self, key: str, expires_in: int = 3600, client_method: str = "get_object", content_type: str = None) -> Optional[str]:
        """Generate a presigned URL for file access or upload."""
        try:
            params = {"Bucket": self.bucket_name, "Key": key}
            if content_type and client_method == "put_object":
                params["ContentType"] = content_type
                
            url = self.s3.generate_presigned_url(
                client_method,
                Params=params,
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Presigned URL error: {e}")
            return None

    def delete_file(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False

    def health_check(self) -> bool:
        """Check S3 connectivity."""
        try:
            self.s3.list_buckets()
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False


_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
