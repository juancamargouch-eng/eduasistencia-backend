import os
from dotenv import load_dotenv
import boto3

load_dotenv()

def debug_keys():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
    )
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    
    print(f"Bucket: {bucket}")
    try:
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=50)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"Key: '{obj['Key']}' | Len: {len(obj['Key'])}")
        else:
            print("No contents.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_keys()
