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
