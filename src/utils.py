import requests
import json
import os

api_key = os.getenv("API_KEY")

def make_get_request():
    """
    Makes a GET request to The Guardian API and returns the response object.
    
    Args:
        None
    
    Returns:
        requests.Response: The HTTP response object returned by the server.
    """
    url = f'https://content.guardianapis.com/search?api-key={api_key}'
    response = requests.get(url)
    return response
    

def retrieve_articles(query):
    url = f'https://content.guardianapis.com/search?q={query}&api-key={api_key}'

    response = requests.get(url)

    result = json.dumps(response.json(), indent=4)

    return result



# https://content.guardianapis.com/search?q=debates
# https://content.guardianapis.com/search?q=debate&tag=politics/politics&from-date=2014-01-01&api-key=test

