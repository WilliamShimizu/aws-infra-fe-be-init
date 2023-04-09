from aws_cdk import core

from backend.cognito.user_pool import CognitoContainer
from frontend.site_hosting import SiteHosting
from backend.backend_apis import CloudFrontLambdaBackend


class MyStack(core.Stack):

    def __init__(self, scope: core.Construct, stage: str, stripe_endpoint: str, stripe_key: str, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        region = core.Stack.of(self).region

        cognito_container = CognitoContainer(scope, 'CognitoUserPool')
        backend_apis = CloudFrontLambdaBackend(scope, stage, region, cognito_container,
                                               stripe_endpoint, stripe_key, 'CloudFrontLambdaBackend')
        site_hosting = SiteHosting(scope, stage, backend_apis.rest_api, 'SiteHosting')


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

check_vars({'stripeEndpoint': stripe_endpoint_secret, 'stripeApiKey': stripe_api_key, 'stage': stage, 'region': region})


MyStack(app, stage, stripe_endpoint_secret, stripe_api_key, f'AwsInfraFeBeInit{region}-{stage}')
app.synth()
