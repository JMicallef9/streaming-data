from src.main import lambda_handler
import pytest
from moto import mock_aws
import boto3
from unittest.mock import patch, Mock
import os
import json
import datetime


@pytest.fixture
def environ_vars():
    """Sets environment variables for integration testing."""
    with patch.dict(
        os.environ, {"BUCKET_NAME": 'test_bucket',
                     "API_KEY": 'test_key',
                     "AWS_REGION": 'eu-west-2'}
                    ):
        yield


@pytest.fixture
def sqs_mock():
    """Creates a mock SQS client."""

    with mock_aws():
        sqs = boto3.client('sqs', region_name='eu-west-2')
        sqs.create_queue(QueueName="guardian_content")
        yield sqs


@pytest.fixture
def s3_mock():
    """Creates a mock S3 client."""

    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        yield s3


@pytest.fixture
def test_event():
    """Creates an event dictionary."""
    event = {"query": "turkey", "broker_ref": "guardian_content"}
    yield event


@pytest.fixture
def mock_get_request():
    """Creates a test response body."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {
                "status": "ok",
                "userTier": "developer",
                "total": 39565,
                "startIndex": 1,
                "pageSize": 10,
                "currentPage": 1,
                "pages": 3957,
                "orderBy": "newest",
                "results": [
                    {
                        "id": (
                            "world/2025/mar/27/bbc-reporter-mark-lowen-"
                            "arrested-and-deported-from-turkey-after"
                            "-covering-protests"
                        ),
                        "type": "article",
                        "sectionId": "world",
                        "sectionName": "World news",
                        "webPublicationDate": "2025-03-27T18:18:12Z",
                        "webTitle": (
                            "BBC reporter arrested and deported from "
                            "Turkey after covering protests"
                        ),
                        "webUrl": (
                            "https://www.theguardian.com/world/2025/mar/27/bbc"
                            "-reporter-mark-lowen-arrested-and-deported-from-"
                            "turkey-after-covering-protests"
                        ),
                        "apiUrl": (
                            "https://content.guardianapis.com/world/2025/mar/"
                            "27/bbc-reporter-mark-lowen-arrested-and-deported"
                            "-from-turkey-after-covering-protests"
                        ),
                        "isHosted": False,
                        "pillarId": "pillar/news",
                        "pillarName": "News"
                    },
                    {
                        "id": (
                            "world/2025/mar/25/eight-journalists-covering-"
                            "anti-government-protests-held-in-turkey"
                        ),
                        "type": "article",
                        "sectionId": "world",
                        "sectionName": "World news",
                        "webPublicationDate": "2025-03-25T16:38:14Z",
                        "webTitle": (
                            "Eight journalists covering anti-government "
                            "protests held in Turkey"
                        ),
                        "webUrl": (
                            "https://www.theguardian.com/world/2025/mar/25/"
                            "eight-journalists-covering-anti-government-"
                            "protests-held-in-turkey"
                        ),
                        "apiUrl": (
                            "https://content.guardianapis.com/world/2025/mar"
                            "/25/eight-journalists-covering-anti-government"
                            "-protests-held-in-turkey"
                        ),
                        "isHosted": False,
                        "pillarId": "pillar/news",
                        "pillarName": "News"
                    },
                    {
                        "id": (
                            "world/2025/mar/24/journalists-among-more-than-"
                            "1100-arrested-in-turkey-crackdown-istanbul"
                        ),
                        "type": "article",
                        "sectionId": "world",
                        "sectionName": "World news",
                        "webPublicationDate": "2025-03-24T17:04:13Z",
                        "webTitle": (
                            "Journalists among more than "
                            "1,100 arrested in Turkey crackdown"
                        ),
                        "webUrl": (
                            "https://www.theguardian.com/world/2025/mar/24/"
                            "journalists-among-more-than-1100-arrested-"
                            "in-turkey-crackdown-istanbul"
                        ),
                        "apiUrl": (
                            "https://content.guardianapis.com/world/2025/mar"
                            "/24/journalists-among-more-than-1100-arrested"
                            "-in-turkey-crackdown-istanbul"
                        ),
                        "isHosted": False,
                        "pillarId": "pillar/news",
                        "pillarName": "News"
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_retrieve_articles():
    """Mocks the response from the retrieve_articles function."""
    with patch("src.main.retrieve_articles") as mock_retrieve:
        mock_retrieve.return_value = [
            {
                'webTitle': 'title',
                'webPublicationDate': 'date',
                'webUrl': 'url'
            }
        ] * 3
        yield mock_retrieve


class TestLambdaHandler:

    def test_saves_file_to_new_bucket(
            self,
            s3_mock,
            sqs_mock,
            test_event,
            mock_get_request,
            environ_vars):
        """Checks that file is saved to new S3 bucket and published to SQS."""
        assert len(s3_mock.list_buckets()['Buckets']) == 0
        assert lambda_handler(test_event, None) == {
            'message': '3 articles published to guardian_content.'
            }

        # Assert S3 bucket was created and file saved
        assert len(s3_mock.list_buckets()['Buckets']) == 1
        response = s3_mock.head_bucket(Bucket='test_bucket')
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        objects = s3_mock.list_objects_v2(Bucket='test_bucket')['Contents']
        assert len(objects) == 1

        # Assert file contents match expected articles
        key = objects[0]['Key']
        s3_object = s3_mock.get_object(Bucket='test_bucket', Key=key)
        content = s3_object['Body'].read().decode('utf-8')
        articles = json.loads(content)
        assert len(articles) == 3
        assert articles[0]['webTitle'] == (
                            "BBC reporter arrested and deported from "
                            "Turkey after covering protests"
                        )
        assert articles[0]["webUrl"] == (
                            "https://www.theguardian.com/world/2025/mar/27/bbc"
                            "-reporter-mark-lowen-arrested-and-deported-from-"
                            "turkey-after-covering-protests"
                        )
        assert articles[0]["webPublicationDate"] == "2025-03-27T18:18:12Z"

        # Assert messages published to SQS
        queue_url = sqs_mock.get_queue_url(
            QueueName='guardian_content'
            )['QueueUrl']

        response = sqs_mock.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10)

        assert len(response['Messages']) == 3

        received_messages = [
            json.loads(message['Body']) for message in response['Messages']
            ]

        assert any(message['webTitle'] == (
                            "BBC reporter arrested and deported from "
                            "Turkey after covering protests"
                        ) for message in received_messages)

    def test_saves_file_to_existing_bucket(
            self,
            s3_mock,
            sqs_mock,
            test_event,
            mock_get_request,
            environ_vars):
        """Checks file is saved to existing S3 bucket and published to SQS."""

        s3_mock.create_bucket(
            Bucket=os.getenv('BUCKET_NAME'),
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

        assert lambda_handler(test_event, None) == {
            'message': '3 articles published to guardian_content.'
            }

        # Assert file was saved to S3 bucket
        objects = s3_mock.list_objects_v2(Bucket='test_bucket')['Contents']
        assert len(objects) == 1

        # Assert file contents match expected articles
        key = objects[0]['Key']
        s3_object = s3_mock.get_object(Bucket='test_bucket', Key=key)
        content = s3_object['Body'].read().decode('utf-8')
        articles = json.loads(content)
        assert len(articles) == 3
        assert articles[0]['webTitle'] == (
                            "BBC reporter arrested and deported from "
                            "Turkey after covering protests"
                        )
        assert articles[0]["webUrl"] == (
                            "https://www.theguardian.com/world/2025/mar/27/bbc"
                            "-reporter-mark-lowen-arrested-and-deported-from-"
                            "turkey-after-covering-protests"
                        )
        assert articles[0]["webPublicationDate"] == "2025-03-27T18:18:12Z"

        # Assert messages published to SQS
        queue_url = sqs_mock.get_queue_url(
            QueueName='guardian_content'
            )['QueueUrl']

        response = sqs_mock.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10)

        assert len(response['Messages']) == 3

        received_messages = [
            json.loads(message['Body']) for message in response['Messages']
            ]

        assert any(message['webTitle'] == (
                            "BBC reporter arrested and deported from "
                            "Turkey after covering protests"
                        ) for message in received_messages)

    def test_no_messages_published_if_limit_reached(
            self,
            s3_mock,
            sqs_mock,
            test_event,
            mock_get_request,
            environ_vars):
        """Checks that no messages are published if today's limit reached."""

        date = str(datetime.date.today())

        s3_mock.create_bucket(
            Bucket=os.getenv('BUCKET_NAME'),
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

        for i in range(50):
            s3_mock.put_object(
                Bucket=os.getenv("BUCKET_NAME"),
                Body=json.dumps({'test': 'data'}),
                Key=f'{date}/filename_{i}'
                )

        assert lambda_handler(test_event, None) == {
            'message': (
                'Rate limit exceeded. No articles published to guardian_content.'
                )
            }

    def test_retrieve_articles_called_without_from_date_field(
            self,
            s3_mock,
            sqs_mock,
            test_event,
            mock_retrieve_articles,
            environ_vars):
        """Checks lambda handler calls retrieve_articles without from_date."""

        lambda_handler(test_event, None)

        mock_retrieve_articles.assert_called_once_with("turkey")

    def test_retrieve_articles_called_with_from_date_field(
            self,
            s3_mock,
            sqs_mock,
            test_event,
            mock_retrieve_articles,
            environ_vars):
        """Checks lambda handler calls retrieve_articles with from_date."""

        test_event['from_date'] = '2025-01-01'

        lambda_handler(test_event, None)

        mock_retrieve_articles.assert_called_once_with("turkey", "2025-01-01")

    def test_error_raised_if_required_fields_missing(
            self,
            s3_mock,
            sqs_mock,
            environ_vars):
        """Checks error is raised if required fields missing from event."""

        query_event = {'query': 'turkey'}

        broker_ref_event = {'broker_ref': 'guardian_content'}

        with pytest.raises(ValueError) as err:
            lambda_handler(query_event, None)
        assert str(err.value) == (
            "Error: required field 'broker_ref' is missing."
            )

        with pytest.raises(ValueError) as err:
            lambda_handler(broker_ref_event, None)
        assert str(err.value) == "Error: required field 'query' is missing."
