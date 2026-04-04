import os
from dotenv import load_dotenv
import boto3

load_dotenv()

def list_all():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
    )
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    
    print(f"Buscando en bucket: {bucket}")
    try:
        response = s3.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"Key: {obj['Key']} | Size: {obj['Size']}")
        else:
            print("El bucket está VACÍO o las credenciales no permiten listar.")
    except Exception as e:
        print(f"ERROR AL LISTAR: {e}")

if __name__ == "__main__":
    list_all()
