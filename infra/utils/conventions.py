from utils.context import Context

PROJECT_NAME = 'aws-infra-fe-be-init'
DOMAIN_NAME = PROJECT_NAME + '.com'


def get_bucket_name(context: Context, purpose: str) -> str:
    """
    Buckets should have deterministic names.
    This will create a bucket name with a deterministic pattern. Unless specifying bucket_name,
    cdk will create a semi-random bucket name, which will add extra steps for deployment and access.
    :param context: Context of the stack
    :param purpose: Some purpose of the bucket, like 'site', or 'user-data', 'lambda-code', etc.
    :return: Returns a string like {project-name}-{purpose}-{region}-{stage}
    """
    return f'{context.project_name}-{purpose}-{context.region}-{context.stage}'


def get_resource_name(suffix: str) -> str:
    """
    Prepends PROJECT_NAME to a resource name. ie, given 'UserPool', returns 'aws-infra-fe-be-init-UserPool'
    :param suffix: Name of the resource.
    :return:
    """
    return f'{PROJECT_NAME}-{suffix}'
