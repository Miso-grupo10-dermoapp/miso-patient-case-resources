import boto3
from boto3.dynamodb.conditions import Key

import app

bucket_name = "cases-resources"


def upload_file(case_id, file_name, file):
    try:
        client = boto3.client('s3')
        client.put_object(Body=file, Bucket=bucket_name, Path= case_id + '/' + file_name, ContentType='image/jpeg')
    except Exception as e:
        raise Exception('cannot upload file on s3: {0}'.format(e))
