from src.utils import (
    retrieve_articles,
    publish_data_to_message_broker,
    check_bucket_exists,
    create_s3_bucket,
    check_number_of_files,
    save_file_to_s3)
import time
import os
from dotenv import load_dotenv
import sys


load_dotenv()


def lambda_handler(event, context):
    """
    Retrieves articles from The Guardian API and publishes them to SQS
    via Lambda execution.

    Args:
        event (dict): The event payload that triggers the Lambda function.
        Includes the following keys:
            - query (str): The search term used in the query to the API.
            - broker_ref (str): The name of the SQS queue
            that articles should be published to.
            - from_date (str, optional): A date used to filter the results
            (ideally in ISO 8601 format e.g. "2021-01-01")

        context (object): Context of the Lambda execution.

    Returns:
        dict: A dictionary containing information about the
        number of articles published.
    """
    query = event.get('query')
    broker_ref = event.get('broker_ref')
    from_date = event.get('from_date')

    if not query:
        raise ValueError("Error: required field 'query' is missing.")

    if not broker_ref:
        raise ValueError("Error: required field 'broker_ref' is missing.")

    bucket_exists = check_bucket_exists()

    if not bucket_exists:
        create_s3_bucket()

    bucket_name = os.getenv('BUCKET_NAME')

    call_count = check_number_of_files(bucket_name)

    if call_count >= 50:
        return {
            'message':
            f'Rate limit exceeded. No articles published to {broker_ref}.'
            }

    if from_date:
        articles = retrieve_articles(query, from_date)
        time.sleep(1)
        count = publish_data_to_message_broker(articles, broker_ref)
        save_file_to_s3(articles, bucket_name)
    else:
        articles = retrieve_articles(query)
        time.sleep(1)
        count = publish_data_to_message_broker(articles, broker_ref)
        save_file_to_s3(articles, bucket_name)

    return {'message': f'{count} articles published to {broker_ref}.'}


if __name__ == '__main__': # pragma: no cover
    args = sys.argv[1:]

    if len(args) < 2:
        print(
            "Error. Arguments should be provided as follows: "
            "python src/main.py <query> <broker_ref> (from_date)"
            )
        sys.exit()

    query = args[0]
    broker_ref = args[1]
    from_date = args[2] if len(args) >= 3 else None

    event = {
        "query": query,
        "broker_ref": broker_ref
    }

    if from_date:
        event["from_date"] = from_date

    lambda_handler(event, context=None)
