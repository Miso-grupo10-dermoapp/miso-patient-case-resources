import json
import os

import boto3
from boto3.dynamodb.conditions import Key
import moto
import pytest
from request_validation_utils import body_properties
import app

BUCKET_NAME = "cases-resources"


@pytest.fixture
def lambda_environment():
    os.environ[app.ENV_TABLE_NAME] = BUCKET_NAME


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def empty_bucket():
    moto_fake = moto.mock_s3()
    try:
        moto_fake.start()
        conn = boto3.resource('s3')
        conn.create_bucket(Bucket=BUCKET_NAME)  # or the name of the bucket you use
        yield conn
    finally:
        moto_fake.stop()

def test_givenValidInputRequestThenReturn200AndValidPersistence(lambda_environment, empty_bucket):
    event = {
            "resource": "/patient/{patient_id}/resource",
    "path": "/patient/123/resource",
    "httpMethod": "POST",
    "headers": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "multipart/form-data; boundary=--------------------------822030104661608197980579",
        "Host": "y3ai500geb.execute-api.us-east-1.amazonaws.com",
        "Postman-Token": "18c4f040-f203-4f81-a346-e6352fecad5a",
        "User-Agent": "PostmanRuntime/7.31.0",
        "X-Amzn-Trace-Id": "Root=1-63fb50ce-25bd50485e2e8e82178bc731",
        "X-Forwarded-For": "186.98.74.225",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https"
    },
    "pathParameters": {
        "patient_id": "123"
    },
    "body": "----------------------------822030104661608197980579\r\nContent-Disposition: form-data; name=\"photo\"; "
            "filename=\"test_file.txt\"\r\nContent-Type: text/plain\r\n\r\ntesting "
            "upload\n\r\n----------------------------822030104661608197980579\r\nContent-Disposition: form-data; "
            "name=\"photo_name\"\r\n\r\n\"test\"\r\n----------------------------822030104661608197980579\r\nContent"
            "-Disposition: form-data; "
            "name=\"case_id\"\r\n\r\n\"case-0012\"\r\n----------------------------822030104661608197980579--\r\n",
    "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 201


def test_givenMissingBodyOnRequestThenReturnError500(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/123/profile",
        "httpMethod": "POST",
        "pathParameters": {
            "patient_id": "123"
        },
        "body": "{}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
    assert '{"message": "cannot proceed with the request error: ' in lambdaResponse['body']


def test_givenMalformedBodyRequestThenReturnError500(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/123/profile",
        "httpMethod": "POST",
        "pathParameters": {
            "patient_id": "123"
        },
        "body": "{\n \"other_field\": \"prof-1\", \"tone_skin\": \"brown\", \"eye_color\": \"blue\",\"hair_coloring\": "
                "\"honey\", \"tan_effect\": \"test\", \"sun_tolerance\": \"low\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
    assert '{"message": "cannot proceed with the request error: Input request is malformed or missing parameters' in lambdaResponse['body']

def test_givenRequestWithoutPatientIDThenReturnError412(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/profile",
        "httpMethod": "POST",
        "pathParameters": {
        },
        "body": "{\n \"other_field\": \"prof-1\", \"tone_skin\": \"brown\", \"eye_color\": \"blue\",\"hair_coloring\": "
                "\"honey\", \"tan_effect\": \"test\", \"sun_tolerance\": \"low\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 412
    assert lambdaResponse['body'] == '{"message": "missing or malformed request body"}'
