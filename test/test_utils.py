from src.utils import retrieve_articles, make_get_request, publish_data_to_message_broker
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
        mock_response.json.return_value = {"response":{"status":"ok","userTier":"developer","total":926,"startIndex":1,"pageSize":10,"currentPage":1,"pages":93,"orderBy":"relevance","results":[{"id":"world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","type":"article","sectionId":"world","sectionName":"World news","webPublicationDate":"2025-04-04T02:00:39Z","webTitle":"EU urged to put human rights centre stage at first central Asia summit","webUrl":"https://www.theguardian.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","apiUrl":"https://content.guardianapis.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","isHosted":False,"pillarId":"pillar/news","pillarName":"News"},{"id":"environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","type":"article","sectionId":"environment","sectionName":"Environment","webPublicationDate":"2023-06-13T10:55:32Z","webTitle":"Turkmenistan moves towards plugging massive methane leaks","webUrl":"https://www.theguardian.com/environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","apiUrl":"https://content.guardianapis.com/environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","isHosted":False,"pillarId":"pillar/news","pillarName":"News"}]}}
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def sqs_mock():
    with mock_aws():
        sqs = boto3.client('sqs', region_name='eu-west-2')
        sqs.create_queue(QueueName="guardian_content")
        yield sqs

class TestMakeGetRequest:

    def test_makes_successful_API_request(self):
        """Ensures that the API can be accessed successfully using the API key."""
        result = make_get_request()
        assert type(result) == dict
        assert result['status_code'] == 200
        response_body = result['response_body']
        assert isinstance(response_body, dict)
        assert 'response' in response_body.keys()
        assert isinstance(response_body['response']['results'], list)
    
    @patch.dict(os.environ, {"API_KEY": "invalid-key"})
    def test_unsuccessful_request_if_invalid_api_key(self):
        """Checks for an unsuccessful request if an invalid API key is used."""
        result = make_get_request()
        assert result['status_code'] == 401
        assert result['response_body']['message'] == 'Unauthorized'
        

class TestRetrieveArticles:
    """Tests for the retrieve_articles function."""

    def test_returns_list_of_dictionaries(self):
        """Ensures that a list of dictionaries is returned."""
        assert isinstance(retrieve_articles("test"), list)
    
    def test_returns_list_of_10_items(self):
        """Ensures that a list of 10 items is returned when a general search term is used."""
        assert len(retrieve_articles("test")) == 10
    
    def test_list_items_contain_correct_dictionary_keys(self):
        """Ensures that the correct information about each article is returned."""
        articles = retrieve_articles("test")
        for article in articles:
            assert list(article.keys()) == ['webPublicationDate', 'webTitle', 'webUrl']
        
    def test_list_items_contain_appropriate_values(self):
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
    
    def test_list_values_are_accurate(self, mock_get_request):
        """Uses a controlled test input to check that the correct information is returned."""
        articles = retrieve_articles("test")

        assert articles[0]['webPublicationDate'] == "2025-04-04T02:00:39Z"
        assert articles[0]['webTitle'] == "EU urged to put human rights centre stage at first central Asia summit"
        assert articles[0]['webUrl'] == "https://www.theguardian.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit"

        assert articles[1]['webPublicationDate'] == "2023-06-13T10:55:32Z"
        assert articles[1]['webTitle'] == "Turkmenistan moves towards plugging massive methane leaks"
        assert articles[1]['webUrl'] == "https://www.theguardian.com/environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks"

    def test_returns_empty_list_if_invalid_query(self):
        """Checks for an empty list if the query produces no results."""
        articles = retrieve_articles("qqqsdfgad")

        assert not articles

    def test_returns_most_recent_articles_first(self):
        """Ensures that the most recent articles are displayed first."""
        articles = retrieve_articles("turkmenistan")

        dates = [datetime.strptime(article['webPublicationDate'], "%Y-%m-%dT%H:%M:%SZ") for article in articles]
        sorted_dates = sorted(dates, reverse=True)

        assert dates == sorted_dates
    
    def test_results_filtered_by_date_if_specified(self):
        """Ensures that date_from parameter is used to filter results."""

        all_articles = retrieve_articles("magcon")

        filtered_articles = retrieve_articles("magcon", '2016-01-01')
        alternative_format = retrieve_articles("magcon", '2016')

        assert all_articles != filtered_articles
        assert all_articles != alternative_format
        assert len(all_articles) > len(filtered_articles)
        assert len(all_articles) > len(alternative_format)
    

    def test_error_message_received_if_invalid_date_format_used(self):
        """Prints error message if user provides invalid date format."""

        with pytest.raises(ValueError) as err:
            retrieve_articles("magcon", '201601')
        assert str(err.value) == 'Invalid date format. Please use a valid ISO format e.g. "2016-01-01" or "2016"'
    
    def test_handles_multiword_search_terms(self):
        """Ensures that the function handles search terms of multiple words."""
        output = retrieve_articles("machine learning")
        assert len(output) == 10

        for article in output:
            assert list(article.keys()) == ['webPublicationDate', 'webTitle', 'webUrl']

    @patch.dict(os.environ, {"API_KEY": "invalid-key"})
    def test_error_raised_if_api_key_is_invalid(self):
        """Ensures that an error is raised if the API key in the environment is invalid."""
        with pytest.raises(ValueError) as err:
            retrieve_articles("test")
        assert str(err.value) == 'Request failed. API key is invalid.'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_error_raised_if_no_api_key_provided(self):
        """Ensures that an error is raised if there is no API key set in the envionment."""
        with pytest.raises(ValueError) as err:
            retrieve_articles("test")
        assert str(err.value) == 'Request failed. API key has not been set.'
    
    def test_handles_timeout_error(self):
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_get.side_effect = requests.exceptions.HTTPError
            with pytest.raises(requests.exceptions.HTTPError) as err:
                retrieve_articles("test")
            assert str(err.value) == 'HTTP request failed.'

@pytest.fixture
def test_data():
    test_data = [{"webPublicationDate": "2023-11-21T11:11:31Z",
                      "webTitle": "Who said what: using machine learning to correctly attribute quotes",
                      "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes"}, {"webPublicationDate":"2025-04-04T02:00:39Z", "webTitle":"EU urged to put human rights centre stage at first central Asia summit","webUrl":"https://www.theguardian.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit"}]
    yield test_data

class TestPublishDataToMessageBroker:
    """Tests for the publish_data_to_message_broker function."""

    def test_publishes_single_message_to_message_broker(self, sqs_mock):
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
    
    def test_publishes_multiple_messages_to_message_broker(self, sqs_mock, test_data):
        """Checks whether multiple dictionaries are successfully published to AWS SQS."""

        broker_reference = "guardian_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=2)

        received_messages = [json.loads(message['Body']) for message in response['Messages']]

        for item in test_data:
            assert item in received_messages
        

    def test_publishes_new_messages_to_existing_queue(self, sqs_mock, test_data):
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


    def test_publishes_messages_to_new_queue(self, sqs_mock, test_data):
        """Checks whether messages are successfully published to a queue that does not yet exist."""

        broker_reference = "new_content"

        publish_data_to_message_broker(test_data, broker_reference)

        queue_url = sqs_mock.get_queue_url(QueueName=broker_reference)['QueueUrl']

        response = sqs_mock.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=2)

        received_messages = [json.loads(message['Body']) for message in response['Messages']]

        for item in received_messages:
            assert item in test_data




        



        