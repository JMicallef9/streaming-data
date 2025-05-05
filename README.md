# Streaming Data

An application that retrieves articles from the [Guardian API](https://open-platform.theguardian.com/) and publishes them to an SQS queue on Amazon Web Services (AWS).

Messages are published to SQS in the following JSON format:
```json
{
    "webPublicationDate": "2023-11-21T11:11:31Z",
    "webTitle": "Who said what: using machine learning to correctly attribute quotes",
    "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes",
    "contentPreview": "The first 1000 characters of the article..."
}
```

The application also stores information about each run in an AWS S3 bucket. 

## Requirements

- Python 3.8+
- An access key for the Guardian API.
- An AWS account.

## Environment Variables

The application requires the following environment variables to be set:

- API_KEY: an access key for the Guardian API.
- AWS_ACCESS_KEY_ID: the AWS access key associated with your AWS account.
- AWS_SECRET_ACCESS_KEY: the AWS secret access key associated with your AWS account.
- AWS_REGION: the region associated with your AWS account.
- BUCKET_NAME: the name you wish to use for the S3 bucket that tracks uses of the application.

## Running the application on the command line

To run the application locally using the command line, follow these instructions:

1. Copy the .env.example file into a .env file using the following command: ```cp .env.example .env```
2. Replace the template values in the .env file with the real environment variables.
3. Run the application with the following command: python src/main.py

## Lambda deployment

The application is packaged and ready to be used as an AWS Lambda function. 

To deploy the application via AWS Lambda, you will need to ensure that all of the environment variables are properly set. You can do this in the following ways:
- configure the environment variables manually in the Lambda section of the AWS console
- or, if deploying via Terraform, use the 'environment' block in your 'aws_lambda_function' resource.

To create the deployment package, first run the following command: make lambda-package

This will create a lambda.zip file containing the code and its associated dependencies. This lambda.zip file is within the memory limits for Python Lambda dependencies.

The lambda.zip file can then be deployed using one of the following methods:

### Option 1: via the AWS Console

1. In the AWS Console, create a new Lambda function (or use an existing one).
2. Under "Code source", select "Upload from .zip file" and then upload the newly created "lambda.zip" file.
3. Select src.main.lambda_handler as the handler name.

### Option 2: via Terraform

1. Create an 'aws_lambda_function' resource.
2. Set the filename as 'lambda.zip'.
3. Set the handler as 'src.main.lambda_handler'.

## Triggering the application

The 'event' that triggers execution of the Lambda function should be in the following format:

{
    "query": "search term",
    "broker_ref": "SQS_queue_name",
    "from_date": "2021-01-01" (optional)
}

The "query" is the search term that will be used to search for articles in the Guardian API. 

The "broker_ref" field is the name of the target SQS queue. Note that this queue does not need to exist already; if it does not exist, it will automatically be created by the application.

The "from_date" field allows optional filtering out of any results older than the given date. Dates should be provided in ISO 8601 format (as above) or as a simple year e.g. "2021". 

The application will retrieve all content returned by the API and publish up to 10 most recent items in JSON format on to the message broker.
