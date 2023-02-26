import boto3
import io

from PIL.Image import Image

import app

bucket_name = "cases-resources"


def upload_file(case_id, file_name, file):
    try:
        client = boto3.client('s3')
        image = Image.frombytes('RGBA', (128,128), file, 'raw')
        client.put_object(Body=image, Bucket=bucket_name, Key= case_id + '/' + file_name, ContentType='image/jpeg')
    except Exception as e:
        raise Exception('cannot upload file on s3: {0}'.format(e))
