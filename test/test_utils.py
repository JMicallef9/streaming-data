from src.utils import retrieve_articles, make_get_request
from unittest.mock import patch, Mock
import json
import os
import re
import pytest
from datetime import datetime


@pytest.fixture
def mock_get_request():
    """Creates a test response body using a specific query."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"response":{"status":"ok","userTier":"developer","total":926,"startIndex":1,"pageSize":10,"currentPage":1,"pages":93,"orderBy":"relevance","results":[{"id":"world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","type":"article","sectionId":"world","sectionName":"World news","webPublicationDate":"2025-04-04T02:00:39Z","webTitle":"EU urged to put human rights centre stage at first central Asia summit","webUrl":"https://www.theguardian.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","apiUrl":"https://content.guardianapis.com/world/2025/apr/04/eu-urged-to-put-human-rights-centre-stage-at-first-central-asia-summit","isHosted":False,"pillarId":"pillar/news","pillarName":"News"},{"id":"environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","type":"article","sectionId":"environment","sectionName":"Environment","webPublicationDate":"2023-06-13T10:55:32Z","webTitle":"Turkmenistan moves towards plugging massive methane leaks","webUrl":"https://www.theguardian.com/environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","apiUrl":"https://content.guardianapis.com/environment/2023/jun/13/turkmenistan-moves-towards-plugging-massive-methane-leaks","isHosted":False,"pillarId":"pillar/news","pillarName":"News"}]}}
        mock_get.return_value = mock_response
        yield mock_get


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

        assert all_articles != filtered_articles
        assert len(all_articles) > len(filtered_articles)




        # what if no query given??? - error

        # invalid date format given by user - error
        # use machine learning as search term - checking multiple word search terms
    


