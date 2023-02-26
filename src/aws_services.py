import boto3
from boto3.dynamodb.conditions import Key

import app
bucket_name="test-bucket"
def upload_file(case_id, file_name, file):
    try:
        client = boto3.client('s3')
        client.upload_file(file, bucket_name, 'folder/index.html')
    except Exception as e:
        raise Exception('cannot upload file on s3: {0}'.format(e))

