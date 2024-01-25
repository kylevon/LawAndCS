import json
import sys
import os
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
# from . import prompter

import prompter
import requests


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    try:
        ip = requests.get("http://checkip.amazonaws.com/")
    except requests.RequestException as e:
        # Send some context about this error to Lambda Logs
        print(e)

        raise e

    try:
        body = json.loads(event.get("body", "{}"))

        # Extract the 'prompt' value from the body
        user_prompt = body.get("prompt", "")

        # Pass the 'prompt' value to your prompter function
        highlighting_raw = prompter.prompt(user_prompt)
        highlighting = []
        for highlight in highlighting_raw:
            highlighting.append(
                {
                    "input_citation": highlight.input_citation,
                    "guideline_citation": highlight.guideline_citation,
                    "explanation": highlight.explanation,
                    "type": "Not implemented"
                }
            )

    except Exception as err:
        highlighting = str(err)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        "body": json.dumps({
            "sentencing_range": [0, 999],
            "remarks": "Not implemented",
            "highlighting": highlighting,
            # "location": ip.text.replace("\n", "")
        }),
    }
