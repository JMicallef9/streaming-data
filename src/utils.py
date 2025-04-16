import requests
import json
import os
import boto3



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
    

def retrieve_articles(query, from_date=None):
    """
    Makes a GET request to The Guardian API using a given query and returns a list of relevant articles.
    
    Args:
        query (str): The search term to use when making the GET request.
    
    Returns:
        list: A list of articles that match the query.
    """

    api_key = os.getenv("API_KEY")

    if not api_key:
        raise ValueError('Request failed. API key has not been set.')

    url = 'https://content.guardianapis.com/search'
    params = {'q': query, 'api-key': api_key, 'from-date': from_date, 'order-by': 'newest'} 

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except requests.RequestException as e:
        raise requests.exceptions.HTTPError(f'HTTP request failed.')
    
    response = data.get('response')

    if not response:
        raise ValueError('Request failed. API key is invalid.')

    result = response.get('results')

    if not isinstance(result, list):
        raise ValueError('Invalid date format. Please use a valid ISO format e.g. "2016-01-01" or "2016"')

    articles = []

    for item in result:
        updated_item = {"webPublicationDate": item['webPublicationDate'], "webTitle": item['webTitle'], "webUrl": item['webUrl']}
        articles.append(updated_item)
    
    return articles

def publish_data_to_message_broker(data, broker_ref):
    """
    Publishes data to a message broker hosted on AWS SQS.

    Args:
        data (list): A list of dictionaries containing information about articles from The Guardian's API.
        broker_ref (str): A reference to a message broker on AWS SQS.
    
    Returns:
        None.
    """

    client = boto3.client('sqs')