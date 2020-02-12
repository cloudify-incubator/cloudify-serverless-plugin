import json


def hello_2(event, context):
    body = {
        "message": "Go Serverless This is Hello 2 ",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
