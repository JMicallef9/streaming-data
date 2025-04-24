import requests
import json
import os
import boto3
import botocore
from datetime import date, datetime


def retrieve_articles(query, from_date=None):
    """
    Makes a GET request to The Guardian API using a given query and
    returns a list of relevant articles.

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
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except requests.RequestException:
        raise requests.exceptions.HTTPError('HTTP request failed.')

    response = data.get('response')

    if not response:
        raise ValueError('Request failed. API key is invalid.')

    result = response.get('results')

    if not isinstance(result, list):
        raise ValueError(
            '''Invalid date format.
            Please use a valid ISO format e.g. "2016-01-01" or "2016"'''
            )

    articles = []

    for item in result:
        updated_item = {
            "webPublicationDate": item['webPublicationDate'],
            "webTitle": item['webTitle'],
            "webUrl": item['webUrl']
            }
        articles.append(updated_item)

    return articles


def publish_data_to_message_broker(data, broker_ref):
    """
    Publishes data to a message broker hosted on AWS SQS.

    Args:
        data (list): A list of dictionaries with information about articles.
        broker_ref (str): A reference to a message broker on AWS SQS.

    Returns:
        int: The number of articles successfully published.
    """
    if not os.getenv("AWS_REGION"):
        raise ValueError('''Request failed.
                         AWS region has not been specified.''')

    client = boto3.client('sqs', region_name=os.getenv("AWS_REGION"))

    try:
        queue_url = client.get_queue_url(QueueName=broker_ref)['QueueUrl']
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
            client.create_queue(
                QueueName=broker_ref,
                Attributes={'MessageRetentionPeriod': '259200'})
            queue_url = client.get_queue_url(QueueName=broker_ref)['QueueUrl']

    if not data:
        return 0

    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        articles = [
            {'Id': str(i),
             "MessageBody": json.dumps(item)} for i, item in enumerate(data)]

        response = client.send_message_batch(
            QueueUrl=queue_url,
            Entries=articles)
        count = len(response.get('Successful'))
        return count

    else:
        raise ValueError('''Invalid data type.
                         Input must be a list of dictionaries.''')


def check_bucket_exists():
    """
    Checks whether an S3 bucket exists with a specific name.

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


def check_number_of_files(bucket_name):
    """
    Checks how many files are in an S3 bucket under today's date.

    Args:
        bucket_name (str): The name of an S3 bucket.
    
    Returns:
        int: The number of files saved under today's date in the S3 bucket.
    """
    client = boto3.client('s3')

    today_date = str(date.today())

    response = client.list_objects_v2(Bucket=bucket_name,
                                      Prefix=today_date)

    contents = response.get('Contents')

    if not contents:
        return 0

    return len(contents)


def save_file_to_s3(data, bucket_name):
    """
    Saves a file to an S3 bucket with information about the articles published to SQS.
    
    Args:
        data (list): A list of articles retrieved from an API.
        bucket_name (str): The S3 bucket in which the file should be saved.
    
    Returns:
        None.
    """
    client = boto3.client('s3')

    today_date = str(date.today())
    timestamp = datetime.now().time().strftime("%H-%M-%S")

    try:
        client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError:
        client.create_bucket(Bucket=bucket_name,
                         CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'})

    client.put_object(Bucket=bucket_name,
                      Body=json.dumps(data),
                      Key=f'{today_date}/{timestamp}')
