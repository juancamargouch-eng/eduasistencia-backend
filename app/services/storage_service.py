import boto3
import os
import hmac
import hashlib
from typing import Optional, Tuple, BinaryIO
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid

class StorageService:
    @staticmethod
    def _get_client():
        from botocore.client import Config
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'},
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )

    @staticmethod
    async def upload_file(file: UploadFile, folder: str = "") -> str:
        """
        Uploads a file to S3 and returns the public URL.
        """
        from fastapi.concurrency import run_in_threadpool
        
        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
        
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        
        # Construct the key (path in bucket)
        key = f"{base_path}/{filename}"
        if folder:
            key = f"{base_path}/{folder}/{filename}"

        try:
            content = await file.read()
            content_type = file.content_type or 'image/jpeg'
            
            # Use run_in_threadpool to prevent blocking the async event loop with synchronous boto3 calls
            await run_in_threadpool(
                s3.put_object,
                Bucket=bucket,
                Key=key,
                Body=content,
                ACL='private',
                ContentType=content_type
            )
            
            return key
        except ClientError as e:
            print(f"DEBUG S3 UPLOAD ERROR: {e}")
            raise Exception(f"Error al subir archivo a S3: {str(e)}")

    @staticmethod
    def delete_file(file_url: str):
        """
        Deletes a file from S3 given its full URL.
        """
        if not file_url or not file_url.startswith("http"):
            return

        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        
        # Extract Key from URL
        # URL format: https://bucket.endpoint/key
        try:
            # Simple way to get key: split by bucket.endpoint/
            endpoint = os.getenv("AWS_S3_ENDPOINT_URL").replace("https://", "")
            
            # Si es solo una key, usarla directo. Si es URL, extraer key.
            key = file_url
            if file_url.startswith("http"):
                parts = file_url.split(f"{bucket}.{endpoint}/")
                if len(parts) > 1:
                    key = parts[1]
            
            s3.delete_object(Bucket=bucket, Key=key)
        except Exception as e:
            print(f"DEBUG S3 DELETE ERROR: {e}")

    @staticmethod
    def get_presigned_url(key: str, expires_in: int = 300) -> str:
        """
        Generates a temporary signed URL for a private object.
        """
        if not key:
            return ""
        
        # If it's already a full URL (legacy or external), return as is
        if key.startswith("http"):
            return key
            
        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        
        try:
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"DEBUG S3 PRESIGNED ERROR: {e}")
            return ""

    @staticmethod
    def check_file_exists(key: str) -> bool:
        """
        Checks if a file exists in the bucket.
        """
        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    @staticmethod
    def download_to_temp_file(key: str) -> Optional[str]:
        """
        Downloads a file from S3 to a temporary local file.
        Returns the path to the temp file or None.
        """
        if not key or key.startswith("http"):
            return None
            
        import tempfile
        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        
        try:
            # Create a named temporary file
            suffix = os.path.splitext(key)[1] or ".jpg"
            # Using delete=False so we can pass the path to Telegram and delete it manually
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                s3.download_fileobj(bucket, key, tmp_file)
                return tmp_file.name
        except Exception as e:
            print(f"DEBUG S3 DOWNLOAD ERROR: {e}")
            return None
    @staticmethod
    def get_signed_proxy_url(key: str) -> str:
        """
        Generates an internal proxy URL with an HMAC signature.
        Used for secure access from Kiosk (no login required).
        """
        if not key: return ""
        
        secret = os.getenv("SECRET_KEY", "eduasistencia-secret-key")
        # Generate signature based on the key
        signature = hmac.new(
            secret.encode(),
            key.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"/api/students/photo-proxy?key={key}&sig={signature}"

    @staticmethod
    def validate_proxy_signature(key: str, signature: str) -> bool:
        """
        Validates if the provided signature matches the key.
        """
        if not key or not signature: return False
        
        secret = os.getenv("SECRET_KEY", "eduasistencia-secret-key")
        expected_sig = hmac.new(
            secret.encode(),
            key.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)

    @staticmethod
    def get_file_stream(key: str) -> Tuple[Optional[BinaryIO], Optional[str], int]:
        """
        Gets a file stream directly from S3.
        Returns (stream, content_type, content_length).
        """
        s3 = StorageService._get_client()
        bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return response['Body'], response.get('ContentType', 'image/jpeg'), response.get('ContentLength', 0)
        except Exception as e:
            print(f"DEBUG S3 STREAM ERROR: {e}")
            return None, None, 0
