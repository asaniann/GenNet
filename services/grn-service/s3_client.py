"""
S3 client for object storage operations
"""

import boto3
import os
from typing import Optional


class S3Client:
    """Client for interacting with S3 object storage"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL")  # For MinIO in dev
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "gennet-data")
    
    def upload_file(self, key: str, file_content: bytes, content_type: Optional[str] = None):
        """Upload file to S3"""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_content,
            ContentType=content_type
        )
    
    def download_file(self, key: str) -> bytes:
        """Download file from S3"""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read()
    
    def delete_file(self, key: str):
        """Delete file from S3"""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for temporary access"""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expiration
        )

