from utils import retrieve_articles, publish_data_to_message_broker

def lambda_handler(event, context):
    """
    Retrieves articles from The Guardian API and publishes them to SQS via Lambda execution.

    Args:
        event (dict): The event payload that triggers the Lambda function. Includes the following keys:
            - query (str): The search term used in the query to the API.
            - from_date (str, optional): A date used to filter the results (ideally in ISO 8601 format e.g. "2021-01-01")
            - broker_ref (str): The name of the SQS queue that articles should be published to.

        context (object): Context of the Lambda execution.
    
    Returns:
        dict: A dictionary containing information about the number of articles published.
    """
    query = event.get('query')
    from_date = event.get('from_date')
    broker_ref = event.get('broker_ref')

    if from_date:
        articles = retrieve_articles(query, from_date)
        publish_data_to_message_broker(articles, broker_ref)
    else:
        articles = retrieve_articles(query)
        publish_data_to_message_broker(articles, broker_ref)
    

    


if __name__ == '__main__':
    lambda_handler()