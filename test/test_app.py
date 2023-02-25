import json
import os

import boto3
from boto3.dynamodb.conditions import Key
import moto
import pytest
from request_validation_utils import body_properties
import app

TABLE_NAME = "dermoapp-patient-cases"


@pytest.fixture
def lambda_environment():
    os.environ[app.ENV_TABLE_NAME] = TABLE_NAME


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def data_table(aws_credentials):
    with moto.mock_dynamodb():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            KeySchema=[
                {"AttributeName": "case_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "case_id", "AttributeType": "S"},
            ],
            TableName=TABLE_NAME,
            BillingMode="PAY_PER_REQUEST"
        )

        yield TABLE_NAME

def test_givenValidInputRequestThenReturn200AndValidPersistence(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/resource",
        "path": "/patient/%7Bpatient_id%7D/resource",
        "httpMethod": "POST",
        "headers": {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "multipart/form-data; boundary=--------------------------659581179206239550902514",
            "Host": "y3ai500geb.execute-api.us-east-1.amazonaws.com",
            "Postman-Token": "6cfcf45f-540d-4b6f-8858-7369b4ede82b",
            "User-Agent": "PostmanRuntime/7.31.0",
            "X-Amzn-Trace-Id": "Root=1-63fa6b85-31b6024f40f0d3b71d09d56e",
            "X-Forwarded-For": "186.98.76.200",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https"
        },
        "multiValueHeaders": {
            "Accept": [
                "*/*"
            ],
            "Accept-Encoding": [
                "gzip, deflate, br"
            ],
            "Content-Type": [
                "multipart/form-data; boundary=--------------------------659581179206239550902514"
            ]
        },
        "pathParameters": {
            "patient_id": "%7Bpatient_id%7D"
        },
        "body": "----------------------------659581179206239550902514\r\nContent-Disposition: form-data; name=\"\"; filename=\"test_file.txt\"\r\nContent-Type: text/plain\r\n\r\ntesting upload\n\r\n----------------------------659581179206239550902514\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ntest\r\n----------------------------659581179206239550902514--\r\n",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    client = boto3.resource("dynamodb", region_name="us-east-1")
    mockTable = client.Table(TABLE_NAME)
    response = mockTable.query(
        KeyConditionExpression=Key('case_id').eq('prof-1')
    )
    items = response['Items']
    if items:
        data = items[0]

    assert lambdaResponse['statusCode'] == 200
    assert data is not None
    for property in body_properties:
        assert data[property] is not None


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
