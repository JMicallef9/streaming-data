from src.utils import retrieve_articles, publish_data_to_message_broker, check_bucket_exists
from unittest.mock import patch, Mock
import json
import os
import re
import pytest
from datetime import datetime
import requests
from moto import mock_aws
import boto3


@pytest.fixture
def mock_get_request():
    """Creates a test response body."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"response":
                                           {"status":"ok","userTier":"developer","total":39565,"startIndex":1,"pageSize":10,"currentPage":1,"pages":3957,"orderBy":"newest","results":[{"id":"world/2025/mar/27/bbc-reporter-mark-lowen-arrested-and-deported-from-turkey-after-covering-protests","type":"article","sectionId":"world","sectionName":"World news","webPublicationDate":"2025-03-27T18:18:12Z","webTitle":"BBC reporter arrested and deported from Turkey after covering protests","webUrl":"https://www.theguardian.com/world/2025/mar/27/bbc-reporter-mark-lowen-arrested-and-deported-from-turkey-after-covering-protests","apiUrl":"https://content.guardianapis.com/world/2025/mar/27/bbc-reporter-mark-lowen-arrested-and-deported-from-turkey-after-covering-protests","isHosted":False,"pillarId":"pillar/news","pillarName":"News"},
                                                                                                                                                                                       {"id":"world/2025/mar/25/eight-journalists-covering-anti-government-protests-held-in-turkey","type":"article","sectionId":"world","sectionName":"World news","webPublicationDate":"2025-03-25T16:38:14Z","webTitle":"Eight journalists covering anti-government protests held in Turkey","webUrl":"https://www.theguardian.com/world/2025/mar/25/eight-journalists-covering-anti-government-protests-held-in-turkey","apiUrl":"https://content.guardianapis.com/world/2025/mar/25/eight-journalists-covering-anti-government-protests-held-in-turkey","isHosted":False,"pillarId":"pillar/news","pillarName":"News"},
                                                                                                                                                                                       {"id":"world/2025/mar/24/journalists-among-more-than-1100-arrested-in-turkey-crackdown-istanbul","type":"article","sectionId":"world","sectionName":"World news","webPublicationDate":"2025-03-24T17:04:13Z","webTitle":"Journalists among more than 1,100 arrested in Turkey crackdown","webUrl":"https://www.theguardian.com/world/2025/mar/24/journalists-among-more-than-1100-arrested-in-turkey-crackdown-istanbul","apiUrl":"https://content.guardianapis.com/world/2025/mar/24/journalists-among-more-than-1100-arrested-in-turkey-crackdown-istanbul","isHosted":False,"pillarId":"pillar/news","pillarName":"News"}
                                                                                                                                                                                                     ]}}
        mock_get.return_value = mock_response
        yield mock_get

@pytest.fixture
def mock_invalid_get_request():
    """Creates a test response body for an invalid request."""
    with patch("requests.get") as mock_invalid_get:
        mock_response = Mock()
        mock_response.json.return_value = {"response":{"status":"ok","userTier":"developer","total":0,"startIndex":0,"pageSize":10,"currentPage":1,"pages":0,"orderBy":"relevance","results":[]}}
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

    def test_returns_list_of_dictionaries(self, mock_get_request, test_api_key):
        """Ensures that a list of dictionaries is returned."""
        assert isinstance(retrieve_articles("test"), list)
    
    def test_returns_correct_number_of_articles(self, mock_get_request, test_api_key):
        """Ensures that a list of the correct length is returned."""
        assert len(retrieve_articles("test")) == 3
    
    def test_list_items_contain_correct_dictionary_keys(self, mock_get_request, test_api_key):
        """Ensures that the correct information about each article is returned."""
        articles = retrieve_articles("test")
        for article in articles:
            assert list(article.keys()) == ['webPublicationDate', 'webTitle', 'webUrl']
        
    def test_list_items_contain_appropriate_values(self, mock_get_request, test_api_key):
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
    
    def test_list_values_are_accurate(self, mock_get_request, test_api_key):
        """Uses a controlled test input to check that the correct information is returned."""
        articles = retrieve_articles("test")

        assert articles[0]['webPublicationDate'] == "2025-03-27T18:18:12Z"
        assert articles[0]['webTitle'] == "BBC reporter arrested and deported from Turkey after covering protests"
        assert articles[0]['webUrl'] == "https://www.theguardian.com/world/2025/mar/27/bbc-reporter-mark-lowen-arrested-and-deported-from-turkey-after-covering-protests"

        assert articles[1]['webPublicationDate'] == "2025-03-25T16:38:14Z"
        assert articles[1]['webTitle'] == "Eight journalists covering anti-government protests held in Turkey"
        assert articles[1]['webUrl'] == "https://www.theguardian.com/world/2025/mar/25/eight-journalists-covering-anti-government-protests-held-in-turkey"

    def test_returns_empty_list_if_invalid_query(self, mock_invalid_get_request, test_api_key):
        """Checks for an empty list if the query produces no results."""
        articles = retrieve_articles("qqqsdfgad")

        assert not articles

    def test_articles_are_not_rearranged(self, mock_get_request, test_api_key):
        """Ensures that the function preserves the order in which articles are retrieved from the API."""

        articles = retrieve_articles("turkey")

        dates = [article['webPublicationDate'] for article in articles]

        assert dates == ["2025-03-27T18:18:12Z", "2025-03-25T16:38:14Z", "2025-03-24T17:04:13Z"]
    
    def test_request_includes_order_by_parameter(self, mock_get_request, test_api_key):
        """Ensures that the order-by parameter is included in API requests."""
        retrieve_articles("turkey")
        args, kwargs = mock_get_request.call_args
        assert kwargs["params"]["order-by"] == 'newest'

    def test_request_includes_from_date_parameter(self, mock_get_request, test_api_key):
        """Ensures that the date-from parameter is included in API requests."""
        retrieve_articles("magcon", "2016-01-01")
        args, kwargs = mock_get_request.call_args
        assert kwargs["params"]["from-date"] == '2016-01-01'

    def test_from_date_omitted_from_request_if_not_provided(self, mock_get_request, test_api_key):
        """Ensures that date_from parameter is omitted from the request if not provided by the user."""

        retrieve_articles("magcon")
        args, kwargs = mock_get_request.call_args
        assert "from-date" not in list(kwargs["params"].keys())

    @patch("requests.get")
    def test_error_message_received_if_invalid_date_format_used(self, mock_get, test_api_key):
        """Prints error message if user provides invalid date format."""
        mock_response = Mock()
        mock_response.json.return_value = {"response":
                                           {"status":"error","message":"Request Failure ElasticError(search_phase_execution_exception,all shards failed,None,None,None,List(ElasticError(parse_exception,failed to parse date field [201601-01-01T00:00:00.000Z] with format [dateOptionalTime]: [failed to parse date field [201601-01-01T00:00:00.000Z] with format [dateOptionalTime]],None,None,None,null,None,None,None,List())),None,Some(can_match),Some(true),List(FailedShard(0,Some(content),Some(uA9rRc_3SVWFDJaYMNO23A),Some(ElasticError(parse_exception,failed to parse date field [201601-01-01T00:00:00.000Z] with format [dateOptionalTime]: [failed to parse date field [201601-01-01T00:00:00.000Z] with format [dateOptionalTime]],None,None,None,null,Some(CausedBy(illegal_argument_exception,failed to parse date field [201601-01-01T00:00:00.000Z] with format [dateOptionalTime],HashMap())),None,None,List())))))"}}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError) as err:
            retrieve_articles("magcon", '201601')

        assert str(err.value) == 'Invalid date format. Please use a valid ISO format e.g. "2016-01-01" or "2016"'
    
    def test_handles_multiword_search_terms(self, mock_get_request, test_api_key):
        """Ensures that the function handles search terms of multiple words."""
        retrieve_articles("machine learning")

        args, kwargs = mock_get_request.call_args
        assert kwargs["params"]["q"] == 'machine learning'

    @patch("requests.get")
    def test_error_raised_if_api_key_is_invalid(self, mock_get, test_api_key):
        """Ensures that an error is raised if an invalid API key is provided."""
        mock_response = Mock()
        mock_response.json.return_value = {'message': 'Unauthorized'}

        mock_get.return_value = mock_response

        with pytest.raises(ValueError) as err:
            retrieve_articles("turkey")

        assert str(err.value) == 'Request failed. API key is invalid.'

    
    @patch.dict(os.environ, {}, clear=True)
    def test_error_raised_if_no_api_key_provided(self):
        """Ensures that an error is raised if there is no API key set in the envionment."""
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
    test_data = [{"webPublicationDate": "2023-11-21T11:11:31Z",
                      "webTitle": "Who said what: using machine learning to correctly attribute quotes",
                      "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes"}, {"webPublicationDate":"2025-04-04T02:00:39Z", "webTitle":"EU urged to put human rights centre stage at first central Asia summit","webUrl":"https://www.theguardian.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit"}]
    yield test_data

@pytest.fixture
def aws_region():
    """Sets AWS region as environment variable."""
    with patch.dict(os.environ, {'AWS_REGION': 'eu-west-2'}):
        yield

class TestPublishDataToMessageBroker:
    """Tests for the publish_data_to_message_broker function."""

    def test_publishes_single_message_to_message_broker(self, sqs_mock, aws_region):
        """Checks whether a single dictionary is successfully published to AWS SQS."""
        test_data = [{"webPublicationDate": "2023-11-21T11:11:31Z",
                      "webTitle": "Who said what: using machine learning to correctly attribute quotes",
                      "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes"}]
        broker_reference = "guardian_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url)

        message = response['Messages'][0]['Body']

        extracted_data = json.loads(message)

        assert test_data[0] == extracted_data
    
    def test_publishes_multiple_messages_to_message_broker(self, sqs_mock, test_data, aws_region):
        """Checks whether multiple dictionaries are successfully published to AWS SQS."""

        broker_reference = "guardian_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=2)

        received_messages = [json.loads(message['Body']) for message in response['Messages']]

        for item in test_data:
            assert item in received_messages
        

    def test_publishes_new_messages_to_existing_queue(self, sqs_mock, test_data, aws_region):
        """Checks whether new messages are successfully published to a queue that already contains messages."""

        broker_reference = "guardian_content"

        publish_data_to_message_broker(test_data, broker_reference)

        new_data = [{"webPublicationDate": "2021-11-21T11:11:31Z",
                      "webTitle": "new: using machine learning to correctly attribute quotes",
                      "webUrl": "https://www.theguardian.com/info/2021/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes"}, {"webPublicationDate":"2021-04-04T02:00:39Z", "webTitle":"new EU urged to put human rights centre stage at first central Asia summit","webUrl":"https://www.theguardian.com/world/2021/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit"}]

        publish_data_to_message_broker(new_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=4)

        received_messages = [json.loads(message['Body']) for message in response['Messages']]

        for item in received_messages:
            assert item in test_data or item in new_data


    def test_publishes_messages_to_new_queue(self, sqs_mock, test_data, aws_region):
        """Checks whether messages are successfully published to a queue that does not yet exist."""

        broker_reference = "new_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=2)

        received_messages = [json.loads(message['Body']) for message in response['Messages']]

        for item in received_messages:
            assert item in test_data

    def test_error_raised_if_invalid_input(self, sqs_mock, aws_region):
        """Checks that an error is raised if data has incorrect data type."""
        broker_reference = "new_content"
        test_data = [['PublicationDate', 'url']]
        with pytest.raises(ValueError) as err:
            publish_data_to_message_broker(test_data, broker_reference)
        assert str(err.value) == 'Invalid data type. Input must be a list of dictionaries.'
    
    def test_error_raised_if_region_not_set_in_environment(self, sqs_mock, test_data):
        """Checks that an error is raised if region not set as environment variable."""
        broker_reference = "new_content"

        with pytest.raises(ValueError) as err:
            publish_data_to_message_broker(test_data, broker_reference)
        assert str(err.value) == 'Request failed. AWS region has not been specified.'
    
    def test_returns_number_of_articles_published(self, sqs_mock, test_data, aws_region):
        """Ensures that the function returns the number of articles published."""

        broker_reference = "new_content"

        assert publish_data_to_message_broker(test_data, broker_reference) == 2
    
    def test_returns_zero_if_no_articles_published(self, sqs_mock, aws_region):
        """Ensures that the function returns zero if passed an empty list."""

        broker_reference = "new_content"
        test_data = []
        assert publish_data_to_message_broker(test_data, broker_reference) == 0

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
        s3_mock.create_bucket(Bucket=os.getenv('BUCKET_NAME'),
                              CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})
        
        assert check_bucket_exists() == True
        


        



        