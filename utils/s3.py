import boto3
from moto import mock_aws
import os
from config.settings import MOCK_S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

def upload_to_mock_s3(file_path: str, youtube_id: str, timestamp: str, format: str):
    try:
        with mock_aws():
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
            )
            try:
                s3_client.head_bucket(Bucket=MOCK_S3_BUCKET)
            except:
                s3_client.create_bucket(Bucket=MOCK_S3_BUCKET)
            
            object_name = f"videos/{youtube_id}_{timestamp}.{format}"
            s3_client.upload_file(file_path, MOCK_S3_BUCKET, object_name)
            s3_url = f"s3://{MOCK_S3_BUCKET}/{object_name}"
            
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': MOCK_S3_BUCKET, 'Key': object_name},
                ExpiresIn=3600
            )
            return s3_url, presigned_url
    except Exception as e:
        raise Exception(f"Failed to upload to mock S3: {str(e)}")