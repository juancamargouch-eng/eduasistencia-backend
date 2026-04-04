import os
from dotenv import load_dotenv
import boto3
from botocore.client import Config

load_dotenv()

def test_read_direct():
    key = "eduasistencia/fotos-estudiantes/f5-ae44-388183edfea7.jpg"
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    
    configs = [
        {"signature_version": "s3v4", "addressing_style": "auto"},
        {"signature_version": "s3v4", "addressing_style": "path"},
        {"signature_version": "s3v4", "addressing_style": "virtual"},
        {"signature_version": None, "addressing_style": "auto"}
    ]
    
    for c in configs:
        print(f"\n--- Probando config: {c} ---")
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
                region_name=os.getenv("AWS_DEFAULT_REGION"),
                config=Config(**c) if c["signature_version"] else None
            )
            resp = s3.get_object(Bucket=bucket, Key=key)
            data = resp['Body'].read(10)
            print(f"¡ÉXITO! Primeros 10 bytes: {data.hex()}")
            return # Si uno funciona, paramos
        except Exception as e:
            print(f"FALLO: {e}")

if __name__ == "__main__":
    test_read_direct()
