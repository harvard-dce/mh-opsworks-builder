from invoke import task, Collection
from invoke.exceptions import Exit
from os import getenv as env
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), '.env'))

STACK_NAME = env('STACK_NAME')
AWS_PROFILE = env('AWS_PROFILE')
LAMBDA_NAME = "builder"


@task
def deploy(ctx):
    cmd = "aws {} s3 ls {}".format(profile_arg(), STACK_NAME)
    exists = ctx.run(cmd, hide=True, warn=True)
    if not exists.ok:
        print("Creating build bucket for {}.".format(STACK_NAME))
        cmd = "aws {} s3api create-bucket --bucket {}".format(profile_arg(), STACK_NAME)
        ctx.run(cmd)

    cmd = "aws {} cloudformation package --template-file template.yml " \
          "--output-template-file serverless-output.yml " \
          "--s3-bucket {}".format(profile_arg(), STACK_NAME)
    ctx.run(cmd)

    with open("buildspec.yml", "r") as f:
        buildspec = f.read()

    cmd = "aws {} cloudformation deploy " \
          "--template-file serverless-output.yml " \
          "--stack-name {} " \
          "--capabilities CAPABILITY_NAMED_IAM "\
          "--parameter-overrides BuildBucketName={} "\
          "--parameter-overrides BuildSpec='{}' "\
        .format(profile_arg(), STACK_NAME, STACK_NAME, buildspec)

    ctx.run(cmd)


@task
def delete(ctx):
    cmd = "aws {} cloudformation delete-stack --stack-name {}"\
        .format(profile_arg(), STACK_NAME)
    res = ctx.run(cmd)

    if res.exited == 0:
        __wait_for(ctx, "delete")

    cmd = "aws {} s3 rm s3://{}/{}/{}.zip"\
        .format(profile_arg(),
                getenv("LAMBDA_CODE_BUCKET"),
                STACK_NAME,
                LAMBDA_NAME)
    ctx.run(cmd)


ns = Collection()

stack_ns = Collection('stack')
stack_ns.add_task(deploy)
stack_ns.add_task(delete)
ns.add_collection(stack_ns)


def getenv(var, required=True):
    val = env(var)
    if required and val is None:
        raise Exit("{} not defined".format(var))
    return val


def profile_arg():
    if AWS_PROFILE is not None:
        return "--profile {}".format(AWS_PROFILE)
    return ""


def __wait_for(ctx, op):
    wait_cmd = ("aws {} cloudformation wait stack-{}-complete "
                "--stack-name {}").format(profile_arg(), op, STACK_NAME)
    print("Waiting for stack {} to complete...".format(op))
    ctx.run(wait_cmd)
    print("Done")
