from src.utils import retrieve_articles, make_get_request
import json

class TestMakeGetRequest:
    """Ensures that the API can be accessed successfully using the given API key."""
    def test_makes_successful_API_request(self):
        result = make_get_request()
        assert type(result) == str
        assert result.status_code == 200
        output = result.json()
        assert isinstance(output, dict)
        assert 'response' in output.keys()
        assert isinstance(output['response']['results'], list)

class TestRetrieveArticles:
    def test_retrieves_articles_from_api(self):
        assert retrieve_articles("bitcoin") == {}

