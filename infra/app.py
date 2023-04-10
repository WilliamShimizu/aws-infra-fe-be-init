from aws_cdk import core

from backend.cognito.user_pool import CognitoContainer
from frontend.site_hosting import SiteHosting
from backend.backend_apis import CloudFrontLambdaBackend
from utils.context import Context, EnvVarKey
from utils.conventions import PROJECT_NAME


class MyStack(core.Stack):

    def __init__(self, scope: core.Construct, context: Context, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        region = core.Stack.of(self).region

        cognito_container = CognitoContainer(self, 'CognitoUserPool', context)
        backend_apis = CloudFrontLambdaBackend(self, context, cognito_container, 'CloudFrontLambdaBackend')
        site_hosting = SiteHosting(self, context, backend_apis.rest_api, 'SiteHosting')


def get_cli_arg(arg_key: str):
    return app.node.try_get_context(arg_key)


def check_vars(variables: dict):
    for key, value in variables.items():
        if not value:
            raise ValueError(f'Value for {key} was null!')


app = core.App()
stripe_endpoint_secret = get_cli_arg('stripeEndpoint')
stripe_api_key = get_cli_arg('stripeApiKey')
stage = get_cli_arg('stage')
region = get_cli_arg('region')
account = get_cli_arg('account')

check_vars({'stripeEndpoint': stripe_endpoint_secret, 'stripeApiKey': stripe_api_key,
            'stage': stage, 'region': region, 'account': account})

env = core.Environment(account=account, region=region)

env_vars = {EnvVarKey.STRIPE_API_KEY: stripe_api_key, EnvVarKey.STRIPE_ENDPOINT: stripe_endpoint_secret}
context = Context(PROJECT_NAME, env, stage, env_vars)

MyStack(app, context, f'AwsInfraFeBeInit-{region}-{stage}', env=env)
app.synth()
