import os
from dotenv import load_dotenv
import boto3
from botocore.client import Config

load_dotenv()

def battle_royale():
    key = "eduasistencia/fotos-estudiantes/f5-ae44-388183edfea7.jpg"
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    endpoint = os.getenv("AWS_S3_ENDPOINT_URL")
    region = os.getenv("AWS_DEFAULT_REGION")
    
    configs = [
        ("V4-Path", Config(signature_version='s3v4', s3={'addressing_style': 'path'})),
        ("V4-Virtual", Config(signature_version='s3v4', s3={'addressing_style': 'virtual'})),
        ("Default", None),
        ("V4-Only", Config(signature_version='s3v4'))
    ]
    
    for name, cfg in configs:
        print(f"\n--- Probando {name} ---")
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=endpoint,
                region_name=region,
                config=cfg
            )
            # Intentar download_fileobj para no escribir a disco
            import io
            f = io.BytesIO()
            s3.download_fileobj(bucket, key, f)
            print(f"¡ÉXITO {name}! Descargados {len(f.getvalue())} bytes.")
            return name
        except Exception as e:
            print(f"FALLO {name}: {e}")

if __name__ == "__main__":
    battle_royale()
