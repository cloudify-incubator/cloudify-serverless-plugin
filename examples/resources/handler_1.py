import json


def hello_1(event, context):
    body = {
        "message": "Go Serverless This is Hello 1 ",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
