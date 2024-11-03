import boto3
from dotenv import load_dotenv
import os
load_dotenv('.env.local')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')  
# def upload_to_s3(file_path, bucket_name, s3_key_folder, s3_key, region='us-east-1'):
#     # Load environment variables from .env.local
#     load_dotenv('.env.local')

#     # Get AWS credentials from environment variables
#     AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
#     AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')

#     # Create an S3 resource
#     s3_resource = boto3.resource(
#         's3', 
#         region_name=region, 
#         aws_access_key_id=AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=AWS_SECRET_ID
#     )
    
#     # Combine the folder and file name to create the full S3 key
#     full_s3_key = os.path.join(s3_key_folder, s3_key)
    
#     # Upload the file to S3
#     try:
#         s3_resource.Bucket(bucket_name).put_object(
#             Key=full_s3_key, 
#             Body=open(file_path, 'rb')
#         )
#         print(f"File {file_path} uploaded to {bucket_name}/{full_s3_key}")
#     except Exception as e:
#         print(f"Failed to upload {file_path} to {bucket_name}/{full_s3_key}: {e}")


def upload_to_s3(file_path, bucket_name, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID, region='us-east-1'):
    print(f"Starting upload process for file: {file_path}")
    
    # Load environment variables from .env.local
    print("Loading environment variables...")
    

    # Get AWS credentials from environment variables

    
    # print(f"AWS_ACCESS_KEY_ID: {'*' * len(AWS_ACCESS_KEY_ID) if AWS_ACCESS_KEY_ID else 'Not found'}")
    # print(f"AWS_SECRET_ID: {'*' * len(AWS_SECRET_ID) if AWS_SECRET_ID else 'Not found'}")
    print("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
    print("AWS_SECRET_ID", AWS_SECRET_ID)
    
    # Create an S3 resource
    print(f"Creating S3 resource for region: {region}")
    try:
        s3_resource = boto3.resource(
            's3', 
            region_name=region, 
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ID
        )
        print("S3 resource created successfully")
    except Exception as e:
        print(f"Failed to create S3 resource: {e}")
        return
    
    # Combine the folder and file name to create the full S3 key
    full_s3_key = os.path.join(s3_key_folder, s3_key)
    print(f"Full S3 key: {full_s3_key}")
    
    # Upload the file to S3
    print(f"Attempting to upload file to bucket: {bucket_name}")
    try:
        with open(file_path, 'rb') as file:
            s3_resource.Bucket(bucket_name).put_object(
                Key=full_s3_key, 
                Body=file
            )
        print(f"File {file_path} uploaded successfully to {bucket_name}/{full_s3_key}")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except boto3.exceptions.S3UploadFailedError as e:
        print(f"Error: S3 upload failed. {e}")
    except Exception as e:
        print(f"Failed to upload {file_path} to {bucket_name}/{full_s3_key}: {e}")

def read_from_s3(bucket_name, s3_key_folder, s3_key, region='us-east-1'):
    # Load environment variables from .env.local
    load_dotenv('.env.local')

    # Get AWS credentials from environment variables
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')

    # Create an S3 client
    s3_client = boto3.client(
        's3', 
        region_name=region, 
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ID
    )
    
    # Combine the folder and file name to create the full S3 key
    full_s3_key = os.path.join(s3_key_folder, s3_key)
    
    # Read the file from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=full_s3_key)
        file_content = response['Body'].read().decode('utf-8')
        print(f"File {full_s3_key} read from {bucket_name}")
        return file_content
    except Exception as e:
        print(f"Failed to read {full_s3_key} from {bucket_name}: {e}")
        return None

# Example usage
# file_path, bucket_name, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID, region='us-east-1'
upload_to_s3(
    file_path='components/GeneratedComponent_1720735534.tsx',
    bucket_name='code-file-storage',
    s3_key_folder="user-name",
    s3_key='GeneratedComponent_1720735534/GeneratedComponent_1720735534.tsx',
    AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
    AWS_SECRET_ID=AWS_SECRET_ID
)

file_content = read_from_s3(
    bucket_name='code-file-storage',
    s3_key_folder="user-name",
    s3_key='GeneratedComponent_1720735534/GeneratedComponent_1720735534.tsx'
)

if file_content:
    print(file_content)