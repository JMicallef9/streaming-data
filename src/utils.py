import requests
import json
import os


def make_get_request():
    """
    Makes a GET request to The Guardian API and returns the response body and status code.
    
    Args:
        None
    
    Returns:
        dict: A dictionary containing the response body and status code.
    """
    api_key = os.getenv("API_KEY")

    url = f'https://content.guardianapis.com/search?api-key={api_key}'
    response = requests.get(url)
    return {"status_code": response.status_code, "response_body": response.json()}
    

def retrieve_articles(query, date=None):
    """
    Makes a GET request to The Guardian API using a given query and returns a list of relevant articles.
    
    Args:
        query (str): The search term to use when making the GET request.
    
    Returns:
        list: A list of articles that match the query.
    """

    api_key = os.getenv("API_KEY")

    url = f'https://content.guardianapis.com/search?q={query}&order-by=newest&api-key={api_key}'

    response = requests.get(url)

    result = response.json()['response']['results']

    articles = []

    for item in result:
        updated_item = {"webPublicationDate": item['webPublicationDate'], "webTitle": item['webTitle'], "webUrl": item['webUrl']}
        articles.append(updated_item)
    
    return articles



# https://content.guardianapis.com/search?q=debates
# https://content.guardianapis.com/search?q=debate&tag=politics/politics&from-date=2014-01-01&api-key=test


