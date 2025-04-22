import requests
import json
import os
import boto3
import botocore



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
    params = {'q': query, 'api-key': api_key, 'order-by': 'newest'} 

    if from_date:
        params['from-date'] = from_date

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
        int: The number of articles successfully published.
    """
    if not os.getenv("AWS_REGION"):
        raise ValueError('Request failed. AWS region has not been specified.')
    
    client = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))

    try:
        queue_url = client.get_queue_url(QueueName=broker_ref)['QueueUrl']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            client.create_queue(QueueName=broker_ref)
            queue_url = client.get_queue_url(QueueName=broker_ref)['QueueUrl']

    if not data:
        return 0

    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        articles = [
            {'Id': str(i), "MessageBody": json.dumps(item)} for i, item in enumerate(data)]

        response = client.send_message_batch(QueueUrl=queue_url, Entries=articles)
        count = len(response.get('Successful'))
        return count

    else:
        raise ValueError("Invalid data type. Input must be a list of dictionaries.")


def check_bucket_exists():
    """
    Checks whether an S3 bucket exists with a name matching the BUCKET_NAME environment variable.
    
    Args:
        None.
    
    Returns:
        bool: True or False depending on whether the bucket exists.
    """
    bucket_name = os.getenv('BUCKET_NAME')

    client = boto3.client('s3')

    if bucket_name:
        try:
            client.head_bucket(Bucket=bucket_name)
            return True
        except botocore.exceptions.ClientError:
            return False
    
    raise ValueError("Error: S3 bucket name (BUCKET_NAME) has not been set.")

def create_s3_bucket():
    """
    Creates an S3 bucket with name matching the BUCKET_NAME environment variable.
    
    Args:
        None.
    
    Returns:
        dict: A dictionary containing information about the successfully created bucket.
    """
    bucket_name = os.getenv('BUCKET_NAME')

    client = boto3.client('s3')

    if bucket_name:
        try:
            client.create_bucket(Bucket=bucket_name,
                         CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

            return {'bucket_name': bucket_name, 'status': 'created'}  
        except botocore.exceptions.ClientError:
            raise ValueError("Error: invalid bucket name provided.") 

    raise ValueError("Error: S3 bucket name (BUCKET_NAME) has not been set.")



# S3 functions:
# 1. does S3 bucket exist at all?
# 2. if no, create one
# 3. if yes, check how many files are in the subfolder representing today's date
# 4. if number of files is less than 50, run and create new file
# 5. if number of files is 50, raise error or don't run