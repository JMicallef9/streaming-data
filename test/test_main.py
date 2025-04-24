# from src.main import lambda_handler
import pytest
from moto import mock_aws
import boto3
from unittest.mock import patch
import os


@pytest.fixture
def sqs_mock():
    """Creates a mock SQS client."""

    with mock_aws():
        sqs = boto3.client('sqs', region_name='eu-west-2')
        sqs.create_queue(QueueName="guardian_content")
        yield sqs


@pytest.fixture
def aws_region():
    """Sets AWS region as environment variable."""
    with patch.dict(os.environ, {'AWS_REGION': 'eu-west-2'}):
        yield


# class TestLambdaHandler:

    # def test_articles_published_to_message_broker_without_date(self,
    #                                                            sqs_mock,
    #                                                            aws_region):
    #     """Checks articles are published without from_date in request body.
    #     test_data = {'query': 'Turkey', 'broker_ref': 'guardian_content'}
    #     assert lambda_handler(test_data, None) == {
    #         'message': '10 articles published to guardian_content.'
    #         }

    # def test_articles_published_to_message_broker_with_date(self,
    #                                                         sqs_mock,
    #                                                         aws_region):
    #     """Checks articles are published and filtered by from_date."""
    #     test_data = {'query': 'Turkey',
    #                  'from_date': '2021-10-10',
    #                  'broker_ref': 'guardian_content'}
    #     assert lambda_handler(test_data, None) == {
    #         'message': '10 articles published to guardian_content.'
    #         }
