## mh-opsworks-builder

Using AWS Serverless + CodeBuild to provide Github webhooks services for auto-building mh-opsworks components. Currently this only includes prepackaging our custom chef cookbook.

## Setup

You'll need Python 2|3, plus the `awscli` package installed. Optionally, for local testing, you can use AWS's [sam](https://github.com/awslabs/aws-sam-local) tool.

The following AWS services are used, so corresponding IAM permissions are necessary:
* Cloudformration
* S3
* API Gateway
* Lambda
* CodeBuild

## Usage

There are three commands to be run, the end result of which will be a Cloudformation stack containing all the resources necessary to act as a webhook that can be plugged into Github.

#### Create a bucket

This is only used for [storing local artifacts](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-cli-package.html) specified in the Cloudformation template (e.g., our Lambda function code).

    aws s3 mb s3://[bucket-name] --region [region]
    
#### Package the Lambda function

    aws cloudformation package \
        --template-file template.yml
        --output-template-file serverless-output.yml
        --s3-bucket [bucket-name]
        
#### Deploy the stack

    aws cloudformation deploy \
        --template-feil serverless-output.yml
        --stack-name mh-opsworks-builder
        --capabilities CAPABILITY_NAMED_IAM
        
#### Register the webhoook

Once the stack has completed buildout, check the resources list in the Cloudformation web console and click the link to the API Gateway instance. Find the API's "Prod" stage `buildcookbook` method and copy the invoke URL. It should look something like [https://foobarbaz.execute-api.us-east-1.amazonaws.com/Prod/buildcookbook](). Copy the URL and head over to the Github project. In "Settings" -> "Webhooks" choose "Add Webhook". Paste the URL into the "Payload URL" field, set the content-type to "application/json", and leave everything else as is. Submit and you're done.