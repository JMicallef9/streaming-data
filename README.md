# Streaming Data

An application that retrieves articles from the [Guardian API](https://open-platform.theguardian.com/) and publishes them to an SQS queue on Amazon Web Services (AWS). 

The application stores information about each run in an AWS S3 bucket. 

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

To run the application locally using the command line, follow these instructions:

1. Copy the .env.example file into a .env file using the following command: cp .env.example .env
2. Replace the template values in the .env file with the real environment variables.
3. Run the application with the following command: python src/main.py

To deploy the application via AWS Lambda, you will need to ensure that all of the environment variables are properly set e.g.
- configure the environment variables manually in the Lambda section of the AWS console
- or, if deploying via Terraform, use the 'environment' block in your 'aws_lambda_function' resource.

## Lambda deployment

The application is packaged and ready to be used as an AWS Lambda function. 

To create the deployment package, first run the following command: make lambda-package

This will create a lambda.zip file containing the code and its associated dependencies. This lambda.zip file is within the memory limits for Python Lambda dependencies.

The lambda.zip file can then be deployed using one of the following methods:

# Option 1: via the AWS Console

1. In the AWS Console, create a new Lambda function (or use an existing one).
2. Under "Code source", select "Upload from .zip file" and then upload the newly created "lambda.zip" file.
3. Select src.main.lambda_handler as the handler name.

# Option 2: via Terraform

1. Create an 'aws_lambda_function' resource.
2. Set the filename as 'lambda.zip'.
3. Set the handler as 'src.main.lambda_handler'.
