import json
import boto3
from os import getenv

BUILD_PROJECT = getenv('COOKBOOK_CODEBUILD_PROJECT')

cb = boto3.client("codebuild")


def handler(event, context):

    print("Event: %s", str(event))

    # handle github webhook handshake
    if "headers" in event and event["headers"].get("X-GitHub-Event") == "ping":
        return {
            "statusCode": 200,
            "body": "pong"
        }

    payload = json.loads(event["body"])

    # "ref" will sometimes be just the branch name and sometimes prefixed with "refs/heads/"
    revision = payload["ref"].replace("refs/heads/", "")

    # ignore branch deletions
    if payload.get("deleted", False):
        return { "statusCode": 204 }

    cb_params = {
        "projectName": BUILD_PROJECT,
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
    is_error = result['ResponseMetadata']['HTTPStatusCode'] != 200

    if is_error:
        msg = "Submit failure on CodeBuild build for %s@%s" % (BUILD_PROJECT, revision)
    else:
        msg = "CodeBuild build submitted for %s@%s" % (BUILD_PROJECT, revision)

    return {
        "statusCode": result['ResponseMetadata']['HTTPStatusCode'],
        "body": msg
    }

