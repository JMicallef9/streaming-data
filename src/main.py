from src.utils import (
    retrieve_articles,
    publish_data_to_message_broker,
    check_bucket_exists,
    create_s3_bucket,
    check_number_of_files,
    save_file_to_s3)
import time
import os


def lambda_handler(event, context):
    """
    Retrieves articles from The Guardian API and publishes them to SQS
    via Lambda execution.

    Args:
        event (dict): The event payload that triggers the Lambda function.
        Includes the following keys:
            - query (str): The search term used in the query to the API.
            - from_date (str, optional): A date used to filter the results
            (ideally in ISO 8601 format e.g. "2021-01-01")
            - broker_ref (str): The name of the SQS queue
            that articles should be published to.

        context (object): Context of the Lambda execution.

    Returns:
        dict: A dictionary containing information about the
        number of articles published.
    """
    query = event.get('query')
    from_date = event.get('from_date')
    broker_ref = event.get('broker_ref')

    bucket_exists = check_bucket_exists()

    if not bucket_exists:
        create_s3_bucket()

    bucket_name = os.getenv('BUCKET_NAME')

    call_count = check_number_of_files(bucket_name)

    if call_count >= 50:
        return {
            'message':
            f'Rate limit exceeded. No articles published to {broker_ref}'
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


if __name__ == '__main__':
    lambda_handler()
