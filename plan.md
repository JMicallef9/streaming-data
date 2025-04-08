retrieve articles from the [Guardian API](https://open-platform.theguardian.com/)
publish articles to a [message broker](https://en.wikipedia.org/wiki/Message_broker)  - AWS SQS

fields:
search term
date_from (optional)
message broker reference (i.e. the ID - "guardian_content")

Retrieve up to 10 MOST RECENT articles

Abide by Guardian API limits:
Up to 1 call per second
Up to 500 calls per day

JSON format for published data:
{
    "webPublicationDate": "2023-11-21T11:11:31Z",
    "webTitle": "Who said what: using machine learning to correctly attribute quotes",
    "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning-to-correctly-attribute-quotes"
}

(optional: add other fields at your discretion)
e.g. "content_preview" in the
message that displays the first few lines of the article content, perhaps the first
1000 characters or so.

Remember:
- PEP8 and security testing
- no credentials recorded in code
- The complete size of the module should not exceed [the memory limits for Python Lambda dependencies](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-package.html)

## Performance criteria
The tool is not expected to handle more than 50 requests per day to the API.

Data should not be persisted in the message broker longer than three days. - I think default in SQS is 14 days???


functions:
make call to Guardian API and retrieve article
convert to correct JSON format
upload to AWS SQS



