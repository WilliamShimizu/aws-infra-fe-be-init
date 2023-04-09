from aws_cdk import core

from backend.apis.api_factory import ApiFactory, ApiMethod, AuthorizationType
from backend.cognito.user_pool import CognitoContainer


class CloudFrontLambdaBackend(core.Construct):

    def __init__(self, scope: core.Construct, stage: str, region: str, cognito_container: CognitoContainer,
                 stripe_endpoint: str, stripe_api_key: str, id: str) -> None:
        super().__init__(scope, id)

        api_factory = ApiFactory(self, stage, region, cognito_container)
        self._rest_api = api_factory.rest_api

        api_factory.add_api('public_hello', {ApiMethod.GET: AuthorizationType.PUBLIC})
        api_factory.add_api('signed_in_hello', {ApiMethod.GET: AuthorizationType.SIGNED_IN})
        api_factory.add_api('paid_hello', {ApiMethod.GET: AuthorizationType.GROUP_MEMBERSHIP})

        stripe_env_vars = {'STRIPE_ENDPOINT': stripe_endpoint, 'STRIPE_API_KEY': stripe_api_key}
        api_factory.add_api('stripe_webhook', {ApiMethod.POST: AuthorizationType.PUBLIC}, stripe_env_vars)

    @property
    def rest_api(self):
        return self._rest_api
