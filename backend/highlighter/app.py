import json
import sys
import os
import asyncio

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

        #api-gateway-simple-proxy-for-lambda-input-format
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    if event["httpMethod"] == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
            "body": json.dumps({}),
        }

    try:
        ip = requests.get("http://checkip.amazonaws.com/")
    except requests.RequestException as e:
        # Send some context about this error to Lambda Logs
        print(e)

        raise e

    try:
        body = json.loads(event.get("body", "{}"))
        print(f"body is: {body}")
        body_second = body.get("body", "{}")
        print(f"Second body is: {body_second}, type is: {type(body_second)}")
        if body_second:
            if type(body_second) is str:
                body = json.loads(body_second)
            elif type(body_second) is dict:
                body = body_second
            else:
                raise TypeError("Some type is not managed for second body.")

        # Extract the 'prompt' value from the body
        user_prompt = body.get("prompt", "")
        factors = [
            "culpability",
            "harm",
            "mitigating_factors",
            "other_aggravating_factors",
            "statutory_aggravating_factors"]

        # factor = body.get("factor", "")
        if user_prompt == "":
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                },
                "body": json.dumps({"error": "Gave empty input.", "body given": body}),
            }

        # if factor not in [
            # "culpability",
            # "harm",
            # "mitigating_factors",
            # "other_aggravating_factors",
            # "statutory_aggravating_factors",
        # ]:
            # return {
                # "statusCode": 400,
                # "headers": {
                    # "Content-Type": "application/json",
                    # "Access-Control-Allow-Origin": "*",
                    # "Access-Control-Allow-Headers": "Content-Type",
                    # "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                # },
                # "body": json.dumps(
                    # {
                        # "error": "The factor must be one of: culpability, harm, mitigating_factors, other_aggravating_factors, statutory_aggravating_factors",
                        # "body given": body,
                    # }
                # ),
            # }

        # Pass the 'prompt' value to your prompter function

        async def async_prompter_prompt(factor, user_prompt):
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, prompter.prompt, factor, user_prompt)
            return result


        async def prompter_curried_func_async(factor, user_prompt):
            try:
                # Set a timeout for the async operation
                entries = await asyncio.wait_for(async_prompter_prompt(factor, user_prompt), timeout=27)
                filted_entries = []
                for entry in entries:
                    if entry["case_text"] == "" or entry["guideline_text"] == "":
                        continue
                    entry["factor"] = factor
                return entries
            except asyncio.TimeoutError:
                print(f"Operation timed out for factor {factor}")
                return []

        async def main(factors, user_prompt):
            tasks = [prompter_curried_func_async(factor, user_prompt) for factor in factors]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        results = [elem for entry in asyncio.run(main(factors, user_prompt)) for elem in entry]
        print(results)

    except Exception as err:
        results = str(err)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(results)
    }
