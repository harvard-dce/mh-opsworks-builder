## mh-opsworks-builder

Using AWS Serverless + CodeBuild to provide Github webhooks services for auto-building mh-opsworks components. This includes prepackaging our custom chef cookbook and opencast builds.

## Setup

You'll need Python 3, plus the `awscli` package installed.

Run `pip install -r requirements.txt`.

Create a `.env` file and fill in the fields from `example.env`.


## Usage

Use `invoke -l` to list the tasks.

Use `invoke stack.deploy` to create or update the CloudFormation stack.

Use `invoke stack.delete` to delete the stack.
        
## Register the webhoook

Once the stack is successfully created, check the resources list in the CloudFormation web console and click the link to the API Gateway instance.Find the API's "Prod" stage `buildcookbook` method and copy the invoke URL. It should look something like [https://foobarbaz.execute-api.us-east-1.amazonaws.com/Prod/buildcookbook]().

##### Github
Copy the URL and head over to the Github project. In "Settings" -> "Webhooks" choose "Add Webhook". Paste the URL into the "Payload URL" field, set the content-type to "application/json". Choose "Let me select individual events" and select "Create" and "Push".

##### Bitbucket
From the Bitbucket project page. Go to "Settings" and under "Workflow" select "Webhooks." Add a webhook with any descriptive name, the URL, and the trigger "repository push." Make sure to mark the new webhook "active" and save.

## Set up Secondary Artifact Buckets

For each secondary bucket:

1. Create a bucket in the secondary account.

2. Get canonical id from the primary account.
By running `aws s3api list-buckets`. Look for "ID" under "Owner" in the response.

3. Add permissions. In the "Permissions" section of the S3 bucket select "Access Control List"
and then "Add Account." Enter the canonical id and check the "Write Objects" box.
Don't forget to save and update the `.env` file with the secondary bucket names.
