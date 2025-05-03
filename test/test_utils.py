from src.utils import (
    retrieve_articles,
    publish_data_to_message_broker,
    check_bucket_exists,
    create_s3_bucket,
    check_number_of_files,
    save_file_to_s3,
    extract_text_from_url
    )
from unittest.mock import patch, Mock
import json
import os
import re
import pytest
import datetime
import requests
from moto import mock_aws
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def mock_get_request():
    """Creates a test response body."""
    with patch("requests.get") as mock_get:
        first_response = Mock()
        first_response.json.return_value = {
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

        second_response = Mock()
        html = """<html><body>
        <div data-gu-name="body">
        <p>The BBC correspondent Mark Lowen has been arrested</p>
        <p>second paragraph</p>
        </div>
        </body></html>
        """
        second_response.text = html
        mock_get.side_effect = [
            first_response, second_response, second_response, second_response
            ]
        yield mock_get


@pytest.fixture
def mock_invalid_get_request():
    """Creates a test response body for an invalid request."""
    with patch("requests.get") as mock_invalid_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {
                "status": "ok",
                "userTier": "developer",
                "total": 0,
                "startIndex": 0,
                "pageSize": 10,
                "currentPage": 1,
                "pages": 0,
                "orderBy": "relevance",
                "results": []}}
        mock_invalid_get.return_value = mock_response
        yield mock_invalid_get


@pytest.fixture
def test_api_key():
    """Sets AWS region as environment variable."""
    with patch.dict(os.environ, {'API_KEY': 'test-key'}):
        yield


@pytest.fixture
def sqs_mock():
    """Creates a mock SQS client."""

    with mock_aws():
        sqs = boto3.client('sqs', region_name='eu-west-2')
        sqs.create_queue(QueueName="guardian_content")
        yield sqs


class TestRetrieveArticles:
    """Tests for the retrieve_articles function."""

    def test_returns_list_of_dicts(self, mock_get_request, test_api_key):
        """Ensures that a list of dictionaries is returned."""
        assert isinstance(retrieve_articles("test"), list)

    def test_returns_correct_number_of_articles(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that a list of the correct length is returned."""
        assert len(retrieve_articles("test")) == 3
        assert mock_get_request.call_count == 4

    def test_list_items_contain_correct_dictionary_keys(
            self,
            mock_get_request,
            test_api_key):
        """Ensures correct information about each article is returned."""
        articles = retrieve_articles("test")
        for article in articles:
            assert list(article.keys()) == [
                'webPublicationDate',
                'webTitle',
                'webUrl',
                'contentPreview'
                ]

    def test_list_items_contain_appropriate_values(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that the correct values are returned for each article."""
        articles = retrieve_articles("test")

        for article in articles:
            date = article['webPublicationDate']
            pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
            assert re.search(pattern, date)

            title = article['webTitle']
            assert isinstance(title, str)

            url = article['webUrl']
            url_pattern = r"^https://www.theguardian.com/"
            assert re.search(url_pattern, url)

            preview = article['contentPreview']
            assert isinstance(preview, str)
            assert preview.startswith(
                'The BBC correspondent Mark Lowen has been arrested'
                )

    def test_list_values_are_accurate(self, mock_get_request, test_api_key):
        """Uses test input to check correct information is returned."""
        articles = retrieve_articles("test")

        assert articles[0]['webPublicationDate'] == "2025-03-27T18:18:12Z"
        assert articles[0]['webTitle'] == (
            "BBC reporter arrested and deported from Turkey "
            "after covering protests")
        assert articles[0]['webUrl'] == (
            "https://www.theguardian.com/world/2025/mar/27/"
            "bbc-reporter-mark-lowen-arrested-and-deported-"
            "from-turkey-after-covering-protests")

        assert articles[1]['webPublicationDate'] == "2025-03-25T16:38:14Z"
        assert articles[1]['webTitle'] == (
            "Eight journalists covering anti-government "
            "protests held in Turkey"
            )
        assert articles[1]['webUrl'] == (
            "https://www.theguardian.com/world/2025/mar/25/"
            "eight-journalists-covering-anti-government-"
            "protests-held-in-turkey")

    def test_returns_empty_list_if_invalid_query(
            self,
            mock_invalid_get_request,
            test_api_key):
        """Checks for an empty list if the query produces no results."""
        articles = retrieve_articles("qqqsdfgad")

        assert not articles

    def test_articles_are_not_rearranged(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that article order is preserved."""

        articles = retrieve_articles("turkey")

        dates = [article['webPublicationDate'] for article in articles]

        assert dates == [
            "2025-03-27T18:18:12Z",
            "2025-03-25T16:38:14Z",
            "2025-03-24T17:04:13Z"
            ]

    def test_request_includes_order_by_parameter(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that the order-by parameter is included in API requests."""
        retrieve_articles("turkey")
        first_call_args = mock_get_request.call_args_list[0]
        args, kwargs = first_call_args
        assert kwargs["params"]["order-by"] == 'newest'

    def test_request_includes_from_date_parameter(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that date-from parameter is included in API requests."""
        retrieve_articles("magcon", "2016-01-01")
        first_call_args = mock_get_request.call_args_list[0]
        args, kwargs = first_call_args
        assert kwargs["params"]["from-date"] == '2016-01-01'

    def test_from_date_omitted_from_request_if_not_provided(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that date_from parameter is omitted if not provided."""

        retrieve_articles("magcon")
        first_call_args = mock_get_request.call_args_list[0]
        args, kwargs = first_call_args
        assert "from-date" not in list(kwargs["params"].keys())

    @patch("requests.get")
    def test_error_message_received_if_invalid_date_format_used(
            self,
            mock_get,
            test_api_key):
        """Prints error message if user provides invalid date format."""
        mock_response = Mock()
        response = {"response": {
            "status": "error",
            "message": (
                "Request Failure ElasticError(search_phase_execution"
                "_exception,all shards failed,None,None,None,List"
                "(ElasticError(parse_exception,failed to parse date"
                "field [201601-01-01T00:00:00.000Z] with format"
                "[dateOptionalTime]: [failed to parse date field"
                "[201601-01-01T00:00:00.000Z] with format [dateOptio"
                "nalTime]],None,None,None,null,None,None,None,List()))"
                ",None,Some(can_match),Some(true),List(FailedShard(0,"
                "Some(content),Some(uA9rRc_3SVWFDJaYMNO23A),Some(Elas"
                "ticError(parse_exception,failed to parse date field "
                "[201601-01-01T00:00:00.000Z] with format [dateOptionalTime]"
                ": [failed to parse date field [201601-01-01T00:00:00.000Z]"
                "with format [dateOptionalTime]],None,None,None,null,Some("
                "CausedBy(illegal_argument_exception,failed to parse date "
                "field [201601-01-01T00:00:00.000Z] with format "
                "[dateOptionalTime],HashMap())),None,None,List())))))"
                )
            }
        }
        mock_response.json.return_value = response
        mock_get.return_value = mock_response
        error_msg = (
            'Invalid date format. Please use a valid ISO format '
            'e.g. "2016-01-01" or "2016"'
            )

        with pytest.raises(ValueError) as err:
            retrieve_articles("magcon", '201601')

        assert str(err.value) == error_msg

    def test_handles_multiword_search_terms(
            self,
            mock_get_request,
            test_api_key):
        """Ensures that the function handles search terms of multiple words."""
        retrieve_articles("machine learning")

        first_call_args = mock_get_request.call_args_list[0]
        args, kwargs = first_call_args
        assert kwargs["params"]["q"] == 'machine learning'

    @patch("requests.get")
    def test_error_raised_if_api_key_is_invalid(self, mock_get, test_api_key):
        """Ensures error is raised if an invalid API key is provided."""
        mock_response = Mock()
        mock_response.json.return_value = {'message': 'Unauthorized'}

        mock_get.return_value = mock_response

        with pytest.raises(ValueError) as err:
            retrieve_articles("turkey")

        assert str(err.value) == 'Request failed. API key is invalid.'

    @patch.dict(os.environ, {}, clear=True)
    def test_error_raised_if_no_api_key_provided(self):
        """Ensures error is raised if no API key set in the envionment."""
        with pytest.raises(ValueError) as err:
            retrieve_articles("test")
        assert str(err.value) == 'Request failed. API key has not been set.'

    def test_handles_timeout_error(self, mock_get_request, test_api_key):
        mock_get_request.side_effect = requests.exceptions.HTTPError
        with pytest.raises(requests.exceptions.HTTPError) as err:
            retrieve_articles("test")
        assert str(err.value) == 'HTTP request failed.'


@pytest.fixture
def test_data():
    """Creates dummy data."""
    test_data = [
        {
            "webPublicationDate": "2023-11-21T11:11:31Z",
            "webTitle": (
                "Who said what: using machine learning"
                "to correctly attribute quotes"
            ),
            "webUrl": (
                "https://www.theguardian.com/info/2023/nov/21/who-said-what-"
                "using-machine-learning-to-correctly-attribute-quotes"
            )
        },
        {
            "webPublicationDate": "2025-04-04T02:00:39Z",
            "webTitle": (
                "EU urged to put human rights centre stage "
                "at first central Asia summit"
            ),
            "webUrl": (
                       "https://www.theguardian.com/world/2025/apr/04/eu-"
                       "urged-to-put-human-rights-centre-stage-at-first-"
                       "central-asia-summit"
                       )
                    }
                ]
    yield test_data


@pytest.fixture
def aws_region():
    """Sets AWS region as environment variable."""
    with patch.dict(os.environ, {'AWS_REGION': 'eu-west-2'}):
        yield


class TestPublishDataToMessageBroker:
    """Tests for the publish_data_to_message_broker function."""

    def test_publishes_single_message_to_message_broker(
            self,
            sqs_mock,
            aws_region):
        """Checks whether single dictionary is published to AWS SQS."""
        test_data = [
            {
                "webPublicationDate": "2023-11-21T11:11:31Z",
                "webTitle": (
                    "Who said what: using machine learning "
                    "to correctly attribute quotes"
                ),
                "webUrl": (
                    "https://www.theguardian.com/info/2023/nov/21/who-"
                    "said-what-using-machine-learning-to-correctly-"
                    "attribute-quotes"
                )
            }
        ]
        broker_reference = "guardian_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue)

        message = response['Messages'][0]['Body']

        extracted_data = json.loads(message)

        assert test_data[0] == extracted_data

    def test_publishes_multiple_messages_to_message_broker(
            self,
            sqs_mock,
            test_data,
            aws_region):
        """Checks whether multiple dictionaries are published to SQS."""

        broker_ref = "guardian_content"

        publish_data_to_message_broker(test_data, broker_ref)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_ref)['QueueUrl']

        response = sqs_mock.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=2)

        received_messages = [
            json.loads(message['Body']) for message in response['Messages']
            ]

        for item in test_data:
            assert item in received_messages

    def test_publishes_new_messages_to_existing_queue(
            self,
            sqs_mock,
            test_data,
            aws_region):
        """Checks whether new messages are published to existing queue."""

        broker_ref = "guardian_content"

        publish_data_to_message_broker(test_data, broker_ref)

        new_data = [
            {
                "webPublicationDate": "2023-11-21T11:11:31Z",
                "webTitle": (
                    "Who said what: using machine learning "
                    "to correctly attribute quotes"
                ),
                "webUrl": (
                    "https://www.theguardian.com/info/2023/nov/21/who-"
                    "said-what-using-machine-learning-to-correctly-"
                    "attribute-quotes"
                )
            }, {
                "webPublicationDate": "2021-04-04T02:00:39Z",
                "webTitle": (
                    "new EU urged to put human rights centre"
                    "stage at first central Asia summit"
                ),
                "webUrl": (
                    "https://www.theguardian.com/world/2021/apr/04/eu-"
                    "urged-to-put-human-rights-centre-stage-at-first-"
                    "central-asia-summit"
                )
            }
        ]

        publish_data_to_message_broker(new_data, broker_ref)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_ref)['QueueUrl']

        response = sqs_mock.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=4)

        received_messages = [
            json.loads(message['Body']) for message in response['Messages']
            ]

        for item in received_messages:
            assert item in test_data or item in new_data

    def test_publishes_messages_to_new_queue(
            self,
            sqs_mock,
            test_data,
            aws_region):
        """Checks messages are successfully published to new queue."""

        broker_ref = "new_content"

        publish_data_to_message_broker(test_data, broker_ref)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_ref)['QueueUrl']

        response = sqs_mock.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=2)

        received_messages = [
            json.loads(message['Body']) for message in response['Messages']
            ]

        for item in received_messages:
            assert item in test_data

    def test_error_raised_if_invalid_input(self, sqs_mock, aws_region):
        """Checks that an error is raised if data has incorrect data type."""
        broker_reference = "new_content"
        test_data = [['PublicationDate', 'url']]
        with pytest.raises(ValueError) as err:
            publish_data_to_message_broker(test_data, broker_reference)
        assert str(err.value) == (
            'Invalid data type. Input must be a list of dictionaries.'
            )

    def test_error_raised_if_region_not_set_in_environment(
            self,
            sqs_mock,
            test_data):
        """Checks error is raised if region not set in environment."""
        broker_reference = "new_content"

        with pytest.raises(ValueError) as err:
            publish_data_to_message_broker(test_data, broker_reference)
        assert str(err.value) == (
            'Request failed. AWS region has not been specified.'
            )

    def test_returns_number_of_articles_published(
            self,
            sqs_mock,
            test_data,
            aws_region):
        """Ensures function returns the number of articles published."""

        broker_reference = "new_content"

        assert publish_data_to_message_broker(test_data, broker_reference) == 2

    def test_returns_zero_if_no_articles_published(self, sqs_mock, aws_region):
        """Ensures that the function returns zero if passed an empty list."""

        broker_reference = "new_content"
        test_data = []
        assert publish_data_to_message_broker(test_data, broker_reference) == 0

    def test_queue_created_with_correct_retention_period(
            self,
            test_data,
            sqs_mock,
            aws_region):
        """Checks that SQS queue has a custom retention period of 3 days."""

        broker_ref = "new_content"

        publish_data_to_message_broker(test_data, broker_ref)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_ref)['QueueUrl']

        attributes = sqs_mock.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["All"]
            )["Attributes"]

        assert attributes['MessageRetentionPeriod'] == "259200"


@pytest.fixture
def s3_mock():
    """Creates a mock S3 client."""

    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')
        yield s3


class TestCheckBucketExists:

    """Tests for the check_bucket_exists function."""

    @patch.dict(os.environ, {'BUCKET_NAME': 'guardian-api-call-tracker'})
    def test_returns_true_if_bucket_exists(self, s3_mock):
        """Checks that the function returns True if the S3 bucket exists."""
        s3_mock.create_bucket(
            Bucket=os.getenv('BUCKET_NAME'),
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

        assert check_bucket_exists() is True

    @patch.dict(os.environ, {'BUCKET_NAME': 'guardian-api-call-tracker'})
    def test_returns_false_if_bucket_does_not_exist(self, s3_mock):
        """Checks that function returns False if S3 bucket does not exist."""
        assert check_bucket_exists() is False

    def test_returns_error_message_if_bucket_name_not_provided(self, s3_mock):
        """Checks error message is received if bucket name not set."""
        with pytest.raises(ValueError) as err:
            check_bucket_exists()
        assert str(err.value) == (
            "Error: S3 bucket name (BUCKET_NAME) has not been set."
            )


class TestCreateS3Bucket:

    """Tests for the create_s3_bucket function."""

    @patch.dict(os.environ, {'BUCKET_NAME': 'guardian-api-call-tracker'})
    def test_creates_s3_bucket(self, s3_mock):
        """Checks that an s3 bucket has been created."""
        assert len(s3_mock.list_buckets()['Buckets']) == 0

        create_s3_bucket()

        assert len(s3_mock.list_buckets()['Buckets']) == 1

    @patch.dict(os.environ, {'BUCKET_NAME': 'guardian-api-call-tracker'})
    def test_bucket_name_matches_environment_variable_name(self, s3_mock):
        """Checks bucket name matches the environment variable."""
        create_s3_bucket()
        response = s3_mock.head_bucket(Bucket='guardian-api-call-tracker')
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200

    @patch.dict(os.environ, {'BUCKET_NAME': 'guardian-api-call-tracker'})
    def test_returns_status_message(self, s3_mock):
        """Checks the status message returned by the function."""
        result = create_s3_bucket()
        assert result['bucket_name'] == 'guardian-api-call-tracker'
        assert result['status'] == 'created'

    def test_error_message_received_if_no_bucket_name_set_in_environment(
            self,
            s3_mock):
        """Checks that an error is raised if no bucket name is set."""
        with pytest.raises(ValueError) as err:
            create_s3_bucket()
        assert str(err.value) == (
            "Error: S3 bucket name (BUCKET_NAME) has not been set."
            )

    @patch.dict(os.environ, {'BUCKET_NAME': 'a...'})
    @patch("boto3.client")
    def test_error_message_received_if_bucket_name_is_invalid(
            self,
            mock_boto_client,
            s3_mock):
        """Checks that error is raised if bucket name breaches S3 rules."""
        mock_client = mock_boto_client.return_value
        mock_client.create_bucket.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'InvalidBucketName',
                    'Message': 'The specified bucket is not valid.'
                }
            },
            operation_name='CreateBucket')

        with pytest.raises(ValueError) as err:
            create_s3_bucket()
        assert str(err.value) == 'Error: invalid bucket name provided.'


class TestCheckNumberOfFiles:
    """Tests for the check_number_of_files function."""

    def test_returns_zero_if_no_files_in_s3_bucket(self, s3_mock):
        """Checks zero is returned if no files in specified bucket."""
        s3_mock.create_bucket(
            Bucket='guardian-api-call-tracker',
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )
        assert check_number_of_files('guardian-api-call-tracker') == 0

    def test_returns_zero_if_no_valid_folder_exists(self, s3_mock):
        """Checks zero is returned if today's folder not in S3 bucket."""
        bucket_name = 'guardian-api-call-tracker'
        s3_mock.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )
        test_data = json.dumps(
            [
                {
                    "webPublicationDate": "2023-11-21T11:11:31Z",
                    "webTitle": (
                        "Who said what: using machine learning to"
                        "correctly attribute quotes"
                    ),
                    "webUrl": (
                        "https://www.theguardian.com/info/2023/nov/"
                        "21/who-said-what-using-machine-learning-to-"
                        "correctly-attribute-quotes"
                    )
                }
            ]
        )
        s3_mock.put_object(Bucket=bucket_name,
                           Body=test_data,
                           Key='filename')
        assert check_number_of_files(bucket_name) == 0

    def test_returns_one_if_file_is_located_in_folder_for_today(self, s3_mock):
        """Checks 1 is returned if file saved under today's date."""
        bucket_name = 'guardian-api-call-tracker'
        s3_mock.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )
        test_data = json.dumps(
            [
                {
                    "webPublicationDate": "2023-11-21T11:11:31Z",
                    "webTitle": (
                        "Who said what: using machine learning to"
                        "correctly attribute quotes"
                    ),
                    "webUrl": (
                        "https://www.theguardian.com/info/2023/nov/"
                        "21/who-said-what-using-machine-learning-to-"
                        "correctly-attribute-quotes"
                    )
                }
            ]
        )
        date = str(datetime.date.today())

        s3_mock.put_object(Bucket=bucket_name,
                           Body=test_data,
                           Key=f'{date}/filename')
        assert check_number_of_files(bucket_name) == 1

    def test_returns_correct_number_if_multiple_files_in_folder(self, s3_mock):
        bucket_name = 'guardian-api-call-tracker'
        s3_mock.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )
        test_data = json.dumps(
            [
                {
                    "webPublicationDate": "2023-11-21T11:11:31Z",
                    "webTitle": (
                        "Who said what: using machine learning to"
                        "correctly attribute quotes"
                    ),
                    "webUrl": (
                        "https://www.theguardian.com/info/2023/nov/"
                        "21/who-said-what-using-machine-learning-to-"
                        "correctly-attribute-quotes"
                    )
                }
            ]
        )
        date = str(datetime.date.today())

        for i in range(20):
            s3_mock.put_object(
                Bucket=bucket_name,
                Body=test_data,
                Key=f'{date}/filename_{i}')
        assert check_number_of_files(bucket_name) == 20


@pytest.fixture()
def datetime_mock():
    """Creates mock timestamp with different values each time it is called."""
    with patch('src.utils.datetime') as mock_dt:

        timestamps = [
            'mock_timestamp_1',
            'mock_timestamp_2',
            'mock_timestamp_3'
            ]
        timestamp_iterator = iter(timestamps)

        def generate_timestamp(arg):
            return next(timestamp_iterator)

        (
            mock_dt.now.return_value.time.return_value.strftime.side_effect
        ) = generate_timestamp

        yield mock_dt


class TestSaveFileToS3:

    """Tests for the save_file_to_s3 function."""

    def test_saves_correct_data_to_existing_s3_bucket(
            self,
            s3_mock,
            test_data,
            datetime_mock):
        """Checks that the correct data is saved to an S3 bucket."""
        bucket_name = 'guardian-api-call-tracker'
        date = str(datetime.date.today())

        s3_mock.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )

        save_file_to_s3(test_data, bucket_name)

        response = s3_mock.get_object(
            Bucket=bucket_name,
            Key=f'{date}/mock_timestamp_1')['Body'].read()

        assert json.loads(response) == test_data

    def test_creates_bucket_and_saves_file_if_bucket_does_not_exist(
            self,
            s3_mock,
            test_data,
            datetime_mock):
        """Ensures function creates an S3 bucket if one does not exist."""
        bucket_name = 'guardian-api-call-tracker'
        date = str(datetime.date.today())
        save_file_to_s3(test_data, bucket_name)

        response = s3_mock.get_object(
            Bucket=bucket_name,
            Key=f'{date}/mock_timestamp_1')['Body'].read()

        assert json.loads(response) == test_data

    def test_saves_multiple_files_to_same_subfolder(
            self,
            s3_mock,
            test_data,
            datetime_mock):
        """Checks that more than one file is saved to the same subfolder."""
        bucket_name = 'guardian-api-call-tracker'
        date = str(datetime.date.today())
        s3_mock.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'eu-west-2'
                }
            )
        for _ in range(3):
            save_file_to_s3(test_data, bucket_name)

        for i in range(1, 4):
            response = s3_mock.get_object(
                Bucket=bucket_name,
                Key=f'{date}/mock_timestamp_{i}')['Body'].read()
            assert json.loads(response) == test_data


@pytest.fixture
def mock_url():
    """Creates a test URL response body."""
    with patch("requests.get") as mock_url:
        mock_response = Mock()
        html = """<html><body>
        <div data-gu-name="body">
        <p>The BBC correspondent Mark Lowen has been arrested</p>
        <p>second paragraph</p>
        </div>
        </body></html>
        """
        mock_response.text = html
        mock_url.return_value = mock_response
        yield mock_url


@pytest.fixture
def mock_error():
    """Mocks requests.get to raise an error."""
    with patch("requests.get") as mock_error:
        mock_error.side_effect = requests.exceptions.RequestException
        yield mock_error


@pytest.fixture
def mock_invalid_body():
    """Creates an invalid response body."""
    with patch("requests.get") as mock_url:
        mock_response = Mock()
        html = """<html><body>
        <div>
        <p>The BBC correspondent Mark Lowen has been arrested</p>
        <p>second paragraph</p>
        </div>
        </body></html>
        """
        mock_response.text = html
        mock_url.return_value = mock_response
        yield mock_url


class TestExtractTextFromUrl:

    """Tests for the extract_text_from_url function."""

    def test_extracts_characters_from_url(self, mock_url):
        """Checks whether the function extracts text successfully."""

        output = extract_text_from_url("www.mock-url.com")
        assert len(output) <= 1000
        assert output.startswith(
            "The BBC correspondent Mark Lowen has been arrested"
            )

    def test_raises_value_error_if_request_fails(self, mock_error):
        """Checks whether error is raised if link is invalid."""

        with pytest.raises(ValueError) as err:
            extract_text_from_url("www.invalid-url.com")
        assert str(err.value) == "Text extraction failed. URL may be invalid."

    def test_raises_value_error_if_incorrect_page_structure(
            self, mock_invalid_body):
        """Checks whether error is raised if page structure is invalid."""

        with pytest.raises(ValueError) as err:
            extract_text_from_url("www.invalid-url.com")
        assert str(err.value) == (
            "Text extraction failed. HTML structure may have changed."
            )
