import json
import boto3
from os import getenv

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

STACK_NAME = getenv('STACK_NAME')
COOKBOOK_BUILD_PROJECT = getenv('COOKBOOK_BUILD_PROJECT')
OPENCAST_BUILD_PROJECT = getenv('OPENCAST_BUILD_PROJECT')


def handler(event, context):

    logger.info("Event: {}".format(str(event)))

    # handle github webhook handshake, default "None" to avoid a key error
    if "headers" in event and event["headers"].get("X-GitHub-Event", None) == "ping":
        return {
            "statusCode": 200,
            "body": "pong"
        }

    payload = json.loads(event["body"])

    if 'ref' in payload:
        project = COOKBOOK_BUILD_PROJECT
        # "ref" will sometimes be just the branch name and sometimes prefixed with "refs/heads/"
        revision = payload["ref"].replace("refs/heads/", "")

        # ignore branch deletions
        if payload.get("deleted", False):
            return {"statusCode": 204}

    elif 'push' in payload:
        logger.info("got bitbucket webhook!")
        project = OPENCAST_BUILD_PROJECT

        new_commit = payload['push']['changes'][0]['new']

        if not new_commit:
            logger.info("Ignore opencast branch deletion.")
            return {"statusCode": 204}

        revision = new_commit['name']

        author = new_commit['target']['author']['raw'].split("<")[0].strip()

        email = new_commit['target']['author']['raw'].split("<")[-1].split(">")[0]

        logger.info("{}, who's email is {}, pushed to the branch named {}"
                    .format(author, email, revision))

    else:
        return {"statusCode": 400}

    status_code, msg = trigger_codebuild(project, revision)

    return {
        "statusCode": status_code,
        "body": msg
    }


def trigger_codebuild(build_project, revision):
    cb = boto3.client("codebuild")

    cb_params = {
        "projectName": build_project,
        "sourceVersion": revision,
        "environmentVariablesOverride": [
            {
                "name": "REVISION",
                "value": revision
            }]
    }

    # forward slash not allowed in S3 key name
    revision = revision.replace("/", "-")

    if "opencast" in build_project:
        cb_params['artifactsOverride'] = {
            'type': 'S3',
            'location': "{}-opencast".format(STACK_NAME),
            'name': revision
        }
    else:
        return 204, "ignoring github requests"  # only temporary!!! while testing

    logger.info("CodeBuild params: %s" % json.dumps(cb_params))

    result = cb.start_build(**cb_params)
    logger.info("CodeBuild response: %s" % str(result))

    status_code = result['ResponseMetadata']['HTTPStatusCode']

    if status_code != 200:
        msg = "Submit failure on CodeBuild build for %s@%s" % (build_project, revision)
    else:
        msg = "CodeBuild build submitted for %s@%s" % (build_project, revision)

    return status_code, msg
