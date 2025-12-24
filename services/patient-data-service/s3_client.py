"""
S3 client for storing patient data files
"""

import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError, BotoCoreError
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for file storage"""
    
    def __init__(self):
        """Initialize S3 client with enhanced error handling"""
        try:
            # Configure with connection pooling
            from botocore.config import Config
            config = Config(
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                connect_timeout=10,
                read_timeout=30,
                max_pool_connections=50
            )
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("AWS_ENDPOINT_URL"),  # For local S3-compatible storage
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                config=config
            )
            self.bucket_name = os.getenv("S3_BUCKET_NAME", "gennet-patient-data")
            self._ensure_bucket_exists()
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            # Bucket doesn't exist, create it
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create S3 bucket: {e}")
                # In development, continue without S3
                self.s3_client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def upload_file(
        self,
        file_path: str,
        s3_key: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload file to S3 with retry logic and enhanced error handling
        
        Args:
            file_path: Local file path
            s3_key: S3 object key
            metadata: Optional metadata dict
            
        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping upload")
            return False
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = {str(k): str(v) for k, v in metadata.items()}
            
            # Use upload_fileobj for better error handling
            with open(file_path, 'rb') as f:
                self.s3_client.upload_fileobj(
                    f,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to upload file to S3 (Code: {error_code}): {error_message}")
            return False
        except BotoCoreError as e:
            logger.error(f"BotoCore error uploading file to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file to S3: {e}")
            return False
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if error
        """
        if not self.s3_client:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted file from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

