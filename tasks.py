import shutil
from invoke import task, Collection
from invoke.exceptions import Exit
from os import getenv as env
from os import symlink
from os.path import join, dirname, exists
from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), '.env'))

STACK_NAME = env('STACK_NAME')
AWS_PROFILE = env('AWS_PROFILE')
LAMBDA_NAME = "builder"


@task
def deploy(ctx):
    __deploy_stack(ctx)


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


def stack_exists(ctx):
    cmd = "aws {} cloudformation describe-stacks --stack-name {}" \
            .format(profile_arg(), STACK_NAME)
    res = ctx.run(cmd, hide=True, warn=True, echo=False)
    return res.exited == 0


def stack_tags():
    tags = "Key=cfn-stack,Value={}".format(STACK_NAME)
    extra_tags = getenv("STACK_TAGS", required=False)
    if extra_tags is not None:
        tags += " " + extra_tags
    return "--tags {}".format(tags)


def __check_required_buckets(ctx):
    required_buckets = [
        getenv('LAMBDA_CODE_BUCKET'),
        getenv('PRIMARY_COOKBOOK_BUCKET'),
        getenv('PRIMARY_OC_BUCKET')
    ]

    for bucket in required_buckets:
        cmd = "aws {} s3 ls {}".format(profile_arg(), bucket)
        exists = ctx.run(cmd, hide=True, warn=True)
        if not exists.ok:
            print("Bucket '{}' does not exist!".format(bucket))
            return


def __wait_for(ctx, op):
    wait_cmd = ("aws {} cloudformation wait stack-{}-complete "
                "--stack-name {}").format(profile_arg(), op, STACK_NAME)
    print("Waiting for stack {} to complete...".format(op))
    ctx.run(wait_cmd)
    print("Done")


def __deploy_stack(ctx):

    if stack_exists(ctx):
        op = "update"
    else:
        op = "create"

    __package(ctx)

    secondary_oc_bucket = getenv('SECONDARY_OC_BUCKET', False)
    secondary_cookbook_bucket = getenv('SECONDARY_COOKBOOK_BUCKET', False)

    with open("buildspec.yml", "r") as f:
        opencast_buildspec = f.read()

    cmd = "aws {} cloudformation deploy " \
          "--capabilities CAPABILITY_NAMED_IAM " \
          "--stack-name {} " \
          "--template-file template.yml " \
          "--parameter-overrides " \
          "PrimaryOCBucket={} " \
          "PrimaryCookbookBucket={} " \
          "LambdaCodeBucket={} " \
          "OpencastBuildSpec='{}' " \
        .format(profile_arg(),
                STACK_NAME,
                getenv('PRIMARY_OC_BUCKET'),
                getenv('PRIMARY_COOKBOOK_BUCKET'),
                getenv('LAMBDA_CODE_BUCKET'),
                opencast_buildspec)

    optional = [('SecondaryOCBucket', secondary_oc_bucket),
                ('SecondaryCookbookBucket', secondary_cookbook_bucket)]

    for key, val in optional:
        if val:
            cmd += "{}={} ".format(key, val)

    res = ctx.run(cmd)

    if res.exited == 0:
        __wait_for(ctx, op)


def __package(ctx, func=LAMBDA_NAME):

    req_file = join(dirname(__file__), 'function-requirements.txt')

    zip_path = join(dirname(__file__), 'dist/{}.zip'.format(func))

    build_path = join(dirname(__file__), 'dist')

    if exists(build_path):
        shutil.rmtree(build_path)

    if exists(req_file):
        ctx.run("pip install -U -r {} -t {}".format(req_file, build_path))
    else:
        ctx.run("mkdir {}".format(build_path))

    module_path = join(dirname(__file__), '{}.py'.format(func))
    module_dist_path = join(build_path, '{}.py'.format(func))
    try:
        print("symlinking {} to {}".format(module_path, module_dist_path))
        symlink(module_path, module_dist_path)
    except FileExistsError:
        pass

    with ctx.cd(build_path):
        ctx.run("zip -r {} .".format(zip_path))

    ctx.run("aws {} s3 cp {} s3://{}/{}/{}.zip".format(
        profile_arg(),
        zip_path,
        getenv('LAMBDA_CODE_BUCKET'),
        STACK_NAME,
        func)
    )
