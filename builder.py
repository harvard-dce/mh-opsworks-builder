import os
import json
import boto3

cb = boto3.client("codebuild")

def handler(event, context):

    print("Event: %s", str(event))

    if event["headers"].get("X-GitHub-Event") == "ping":
        return {
            "statusCode": 200,
            "body": "pong"
        }

    build_project = os.environ['COOKBOOK_CODEBUILD_PROJECT']
    payload = json.loads(event["body"])
    revision = payload["ref"].split("/", 2)[-1]

    cb_params = {
        "projectName": build_project,
        "sourceVersion": revision,
        "environmentVariablesOverride": [
            { 
                "name": "REVISION",
                "value": revision
            }
        ]
    }

    print("Codebuild params: %s" % json.dumps(cb_params))

    result = cb.start_build(**cb_params)
    print("Codebuild response: %s" % str(result))

    return {
        "statusCode": result['ResponseMetadata']['HTTPStatusCode'],
        "body": "Build initiated"
    }
