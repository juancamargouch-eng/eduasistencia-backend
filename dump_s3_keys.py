import os
from dotenv import load_dotenv
import boto3

load_dotenv()

def dump_keys():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
    )
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    
    all_keys = []
    continuation_token = None
    
    try:
        while True:
            params = {'Bucket': bucket}
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            response = s3.list_objects_v2(**params)
            if 'Contents' in response:
                for obj in response['Contents']:
                    all_keys.append(obj['Key'])
            
            if response.get('IsTruncated'):
                continuation_token = response['NextContinuationToken']
            else:
                break
        
        with open("all_s3_keys.txt", "w", encoding="utf-8") as f:
            for k in all_keys:
                f.write(f"{k}\n")
        print(f"Dumped {len(all_keys)} keys to all_s3_keys.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_keys()
