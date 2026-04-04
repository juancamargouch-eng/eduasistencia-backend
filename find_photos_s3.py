import os
from dotenv import load_dotenv
import boto3

load_dotenv()

def find_photos():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
    )
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
    
    print(f"Buscando fotos con prefijo '{base_path}' en bucket: {bucket}")
    try:
        # Primero listar con prefijo
        response = s3.list_objects_v2(Bucket=bucket, Prefix=base_path)
        if 'Contents' in response:
            print(f"ENCONTRADOS {len(response['Contents'])} archivos con el prefijo.")
            for obj in response['Contents'][:10]: # Solo mostrar 10
                print(f"Key: {obj['Key']}")
        else:
            print("No se encontraron archivos con ese prefijo. Buscando en TODO el bucket...")
            # Listar todo y buscar subcadenas si falla con prefijo
            full_response = s3.list_objects_v2(Bucket=bucket)
            if 'Contents' in full_response:
                edu_files = [obj['Key'] for obj in full_response['Contents'] if 'eduasistencia' in obj['Key']]
                print(f"Encontrados {len(edu_files)} archivos que contienen 'eduasistencia' en cualquier parte.")
                for k in edu_files[:10]:
                    print(f"Key: {k}")
            else:
                print("El bucket parece estar vacío o inaccesible.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    find_photos()
