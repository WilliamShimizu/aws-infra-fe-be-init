from utils.context import Context

PROJECT_NAME = 'aws-infra-fe-be-init'


def get_bucket_name(context: Context, purpose: str, regional: bool):
    if regional:
        return f'{context.project_name}-{purpose}-{context.region}-{context.stage}'
    return f'{context.project_name}-{purpose}-{context.stage}'
