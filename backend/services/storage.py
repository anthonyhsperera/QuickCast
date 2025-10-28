import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import os
import uuid
from datetime import datetime, timedelta

class R2Storage:
    """Handles file uploads to Cloudflare R2 storage"""

    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str,
                 bucket_name: str, public_url: str = None):
        """
        Initialize R2 storage client

        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: Name of the R2 bucket
            public_url: Optional public bucket URL (e.g., https://pub-xxxxx.r2.dev)
        """
        self.account_id = account_id
        self.bucket_name = bucket_name
        self.public_url = public_url

        # Configure R2 endpoint
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        # Initialize S3 client with R2 endpoint
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=BotoConfig(
                signature_version='s3v4',
                region_name='auto'
            )
        )

    def generate_share_id(self) -> str:
        """Generate a unique share ID (short and URL-friendly)"""
        # Use first 8 characters of UUID for short, readable IDs
        return str(uuid.uuid4())[:8]

    def upload_podcast(self, file_path: str, share_id: str = None, metadata: dict = None) -> dict:
        """
        Upload podcast file to R2

        Args:
            file_path: Path to the podcast WAV file
            share_id: Optional custom share ID (generated if not provided)
            metadata: Optional metadata dict with article info

        Returns:
            dict with share_id, r2_key, and url
        """
        if not share_id:
            share_id = self.generate_share_id()

        # Use share_id as filename (with .wav extension)
        r2_key = f"{share_id}.wav"

        # Prepare S3 metadata (must be strings)
        s3_metadata = {}
        if metadata:
            if metadata.get('title'):
                s3_metadata['title'] = str(metadata['title'])[:1024]  # S3 metadata limit
            if metadata.get('author'):
                s3_metadata['author'] = str(metadata['author'])[:1024]
            if metadata.get('url'):
                s3_metadata['source-url'] = str(metadata['url'])[:1024]
            if metadata.get('duration'):
                s3_metadata['duration'] = str(metadata['duration'])

        # Add creation timestamp
        s3_metadata['created-at'] = datetime.utcnow().isoformat()
        s3_metadata['expires-at'] = (datetime.utcnow() + timedelta(days=3)).isoformat()

        try:
            # Upload file to R2
            with open(file_path, 'rb') as f:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=r2_key,
                    Body=f,
                    ContentType='audio/wav',
                    Metadata=s3_metadata
                )

            # Generate URL for the file
            if self.public_url:
                # Use public bucket URL if configured
                url = f"{self.public_url}/{r2_key}"
            else:
                # Generate presigned URL (valid for 3 days)
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': r2_key},
                    ExpiresIn=259200  # 3 days in seconds
                )

            return {
                'share_id': share_id,
                'r2_key': r2_key,
                'url': url,
                'uploaded_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=3)).isoformat()
            }

        except ClientError as e:
            raise Exception(f"Failed to upload to R2: {str(e)}")

    def get_file_metadata(self, share_id: str) -> dict:
        """
        Get metadata for a shared file

        Args:
            share_id: The share ID

        Returns:
            dict with metadata
        """
        r2_key = f"{share_id}.wav"

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=r2_key
            )

            metadata = response.get('Metadata', {})

            # Generate URL for the file
            if self.public_url:
                url = f"{self.public_url}/{r2_key}"
            else:
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': r2_key},
                    ExpiresIn=3600  # 1 hour for viewing
                )

            return {
                'share_id': share_id,
                'title': metadata.get('title', 'QuickCast Podcast'),
                'author': metadata.get('author'),
                'source_url': metadata.get('source-url'),
                'duration': float(metadata.get('duration', 0)) if metadata.get('duration') else None,
                'audio_url': url,
                'created_at': metadata.get('created-at'),
                'expires_at': metadata.get('expires-at'),
                'exists': True
            }

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return {'exists': False, 'error': 'Podcast not found or expired'}
            raise Exception(f"Failed to get metadata from R2: {str(e)}")

    def delete_file(self, share_id: str) -> bool:
        """
        Delete a shared file (mainly for testing - lifecycle policy handles auto-deletion)

        Args:
            share_id: The share ID

        Returns:
            bool indicating success
        """
        r2_key = f"{share_id}.wav"

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=r2_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete from R2: {str(e)}")
