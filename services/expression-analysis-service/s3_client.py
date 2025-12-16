"""
S3 client for Expression Analysis Service
Reuses pattern from other services
"""

import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for file storage"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "gennet-patient-data")
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create S3 bucket: {e}")
                self.s3_client = None
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3"""
        if not self.s3_client:
            return False
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False

