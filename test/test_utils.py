from src.utils import retrieve_articles, make_get_request
from unittest.mock import patch
import json
import os

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
        

# class TestRetrieveArticles:
#     def test_returns_list_of_dictionaries(self):
#         assert isinstance(retrieve_articles("test"), list)

