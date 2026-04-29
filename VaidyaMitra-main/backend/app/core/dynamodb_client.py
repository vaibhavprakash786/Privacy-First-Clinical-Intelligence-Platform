"""
DynamoDB Client

AWS DynamoDB data layer for VAIDYAMITRA.
Supports both AWS DynamoDB and DynamoDB Local for development.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


# Table names
TABLE_PATIENTS = f"{settings.DYNAMODB_TABLE_PREFIX}patients"
TABLE_PATIENT_VISITS = f"{settings.DYNAMODB_TABLE_PREFIX}patient_visits"
TABLE_CLINICAL_VISITS = f"{settings.DYNAMODB_TABLE_PREFIX}clinical_visits"
TABLE_CLINICAL_SUMMARIES = f"{settings.DYNAMODB_TABLE_PREFIX}clinical_summaries"
TABLE_DISEASE_PREDICTIONS = f"{settings.DYNAMODB_TABLE_PREFIX}disease_predictions"
TABLE_DRUG_KNOWLEDGE_BASE = f"{settings.DYNAMODB_TABLE_PREFIX}drug_knowledge_base"
TABLE_PRIVACY_AUDIT_LOGS = f"{settings.DYNAMODB_TABLE_PREFIX}privacy_audit_logs"
TABLE_CHANGE_REPORTS = f"{settings.DYNAMODB_TABLE_PREFIX}change_reports"
TABLE_RAG_EMBEDDINGS = f"{settings.DYNAMODB_TABLE_PREFIX}rag_embeddings"
TABLE_AI_CACHE = f"{settings.DYNAMODB_TABLE_PREFIX}ai_cache"
TABLE_CLINICAL_REPORTS = f"{settings.DYNAMODB_TABLE_PREFIX}clinical_reports"


class DynamoDBClient:
    """DynamoDB client with table operations for all VAIDYAMITRA data."""

    def __init__(self):
        kwargs = {"region_name": settings.AWS_REGION}
        if settings.DYNAMODB_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL
        if settings.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.dynamodb = boto3.resource("dynamodb", **kwargs)
        self.client = boto3.client("dynamodb", **kwargs)
        self._tables_created = False
        logger.info(
            f"DynamoDB client initialized "
            f"(endpoint: {settings.DYNAMODB_ENDPOINT_URL or 'AWS'})"
        )

    def _convert_to_dynamodb(self, obj: Any) -> Any:
        """Convert Python types to DynamoDB-compatible types."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._convert_to_dynamodb(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_to_dynamodb(i) for i in obj]
        return obj

    def _convert_from_dynamodb(self, obj: Any) -> Any:
        """Convert DynamoDB types back to Python types."""
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        if isinstance(obj, dict):
            return {k: self._convert_from_dynamodb(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_from_dynamodb(i) for i in obj]
        return obj

    def ensure_tables(self):
        """Create all required tables if they don't exist."""
        if self._tables_created:
            return

        table_definitions = [
            {
                "TableName": TABLE_PATIENTS,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_PATIENT_VISITS,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "visit_id", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                    {"AttributeName": "visit_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_CLINICAL_VISITS,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "visit_id", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                    {"AttributeName": "visit_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_CLINICAL_SUMMARIES,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "summary_id", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                    {"AttributeName": "summary_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_DISEASE_PREDICTIONS,
                "KeySchema": [
                    {"AttributeName": "prediction_id", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "prediction_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_DRUG_KNOWLEDGE_BASE,
                "KeySchema": [
                    {"AttributeName": "drug_id", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "drug_id", "AttributeType": "S"},
                    {"AttributeName": "brand_name", "AttributeType": "S"},
                    {"AttributeName": "generic_name", "AttributeType": "S"},
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "brand_name_index",
                        "KeySchema": [
                            {"AttributeName": "brand_name", "KeyType": "HASH"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                    {
                        "IndexName": "generic_name_index",
                        "KeySchema": [
                            {"AttributeName": "generic_name", "KeyType": "HASH"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                ],
            },
            {
                "TableName": TABLE_PRIVACY_AUDIT_LOGS,
                "KeySchema": [
                    {"AttributeName": "event_id", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "event_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_CHANGE_REPORTS,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "report_id", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                    {"AttributeName": "report_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_RAG_EMBEDDINGS,
                "KeySchema": [
                    {"AttributeName": "doc_id", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "doc_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_CLINICAL_REPORTS,
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"},
                    {"AttributeName": "report_id", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "patient_id", "AttributeType": "S"},
                    {"AttributeName": "report_id", "AttributeType": "S"},
                ],
            },
            {
                "TableName": TABLE_AI_CACHE,
                "KeySchema": [
                    {"AttributeName": "cache_key", "KeyType": "HASH"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "cache_key", "AttributeType": "S"},
                ],
                "TTL": {
                    "AttributeName": "expires_at",
                    "Enabled": True,
                },
            },
        ]

        existing = self._get_existing_tables()
        for table_def in table_definitions:
            name = table_def["TableName"]
            if name in existing:
                logger.debug(f"Table {name} already exists")
                continue

            create_params = {
                "TableName": name,
                "KeySchema": table_def["KeySchema"],
                "AttributeDefinitions": table_def["AttributeDefinitions"],
                "BillingMode": "PAY_PER_REQUEST",
            }

            # If GSIs are defined, add them
            if "GlobalSecondaryIndexes" in table_def:
                # For PAY_PER_REQUEST, remove ProvisionedThroughput from GSIs
                gsis = []
                for gsi in table_def["GlobalSecondaryIndexes"]:
                    gsi_copy = {k: v for k, v in gsi.items() if k != "ProvisionedThroughput"}
                    gsis.append(gsi_copy)
                create_params["GlobalSecondaryIndexes"] = gsis

            try:
                self.client.create_table(**create_params)
                logger.info(f"Created table: {name}")

                # Enable TTL if configured
                if "TTL" in table_def:
                    try:
                        # Wait for table to become active
                        waiter = self.client.get_waiter("table_exists")
                        waiter.wait(TableName=name, WaiterConfig={"Delay": 2, "MaxAttempts": 10})
                        self.client.update_time_to_live(
                            TableName=name,
                            TimeToLiveSpecification={
                                "Enabled": table_def["TTL"]["Enabled"],
                                "AttributeName": table_def["TTL"]["AttributeName"],
                            },
                        )
                        logger.info(f"Enabled TTL on table: {name}")
                    except Exception as ttl_err:
                        logger.warning(f"Could not enable TTL on {name}: {ttl_err}")

            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceInUseException":
                    logger.debug(f"Table {name} already exists")
                else:
                    logger.error(f"Error creating table {name}: {e}")

        self._tables_created = True
        logger.info("All DynamoDB tables ensured")

    def _get_existing_tables(self) -> List[str]:
        try:
            response = self.client.list_tables()
            return response.get("TableNames", [])
        except Exception as e:
            logger.warning(f"Could not list tables: {e}")
            return []

    # --- CRUD Operations ---

    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """Put an item into a table."""
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item=self._convert_to_dynamodb(item))
            return True
        except Exception as e:
            logger.error(f"Error putting item in {table_name}: {e}")
            return False

    def get_item(self, table_name: str, key: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get an item from a table."""
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key=key)
            item = response.get("Item")
            return self._convert_from_dynamodb(item) if item else None
        except Exception as e:
            logger.error(f"Error getting item from {table_name}: {e}")
            return None

    def query_items(
        self,
        table_name: str,
        key_condition: str,
        expression_values: Dict[str, Any],
        index_name: Optional[str] = None,
        limit: int = 50,
        scan_forward: bool = False,
    ) -> List[Dict[str, Any]]:
        """Query items from a table."""
        try:
            table = self.dynamodb.Table(table_name)
            params = {
                "KeyConditionExpression": key_condition,
                "ExpressionAttributeValues": self._convert_to_dynamodb(expression_values),
                "Limit": limit,
                "ScanIndexForward": scan_forward,
            }
            if index_name:
                params["IndexName"] = index_name

            response = table.query(**params)
            items = response.get("Items", [])
            return [self._convert_from_dynamodb(item) for item in items]
        except Exception as e:
            logger.error(f"Error querying {table_name}: {e}")
            return []

    def scan_items(
        self,
        table_name: str,
        filter_expression: Optional[str] = None,
        expression_values: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Scan items from a table."""
        try:
            table = self.dynamodb.Table(table_name)
            params = {"Limit": limit}
            if filter_expression:
                params["FilterExpression"] = filter_expression
            if expression_values:
                params["ExpressionAttributeValues"] = self._convert_to_dynamodb(
                    expression_values
                )

            response = table.scan(**params)
            items = response.get("Items", [])
            return [self._convert_from_dynamodb(item) for item in items]
        except Exception as e:
            logger.error(f"Error scanning {table_name}: {e}")
            return []

    def delete_item(self, table_name: str, key: Dict[str, str]) -> bool:
        """Delete an item from a table."""
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from {table_name}: {e}")
            return False

    def health_check(self) -> bool:
        """Check DynamoDB connectivity."""
        try:
            self.client.list_tables(Limit=1)
            return True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")
            return False


# Singleton instance
_db_client: Optional[DynamoDBClient] = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get or create the singleton DynamoDB client."""
    global _db_client
    if _db_client is None:
        _db_client = DynamoDBClient()
    return _db_client
