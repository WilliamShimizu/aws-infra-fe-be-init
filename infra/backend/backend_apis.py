from aws_cdk import core

from backend.apis.api_factory import ApiFactory, ApiMethod, AuthorizationType
from backend.cognito.user_pool import CognitoContainer
from utils.context import Context, EnvVarKey


class CloudFrontLambdaBackend(core.Construct):

    def __init__(self, scope: core.Construct, context: Context, cognito_container: CognitoContainer, id: str) -> None:
        super().__init__(scope, id)

        api_factory = ApiFactory(scope, context, cognito_container)
        self._rest_api = api_factory.rest_api

        api_factory.add_api('public_hello', {ApiMethod.GET: AuthorizationType.PUBLIC})
        api_factory.add_api('signed_in_hello', {ApiMethod.GET: AuthorizationType.SIGNED_IN})
        api_factory.add_api('paid_hello', {ApiMethod.GET: AuthorizationType.GROUP_MEMBERSHIP})

        stripe_env_vars = {EnvVarKey.STRIPE_ENDPOINT.value: context.get_env_var(EnvVarKey.STRIPE_ENDPOINT),
                           EnvVarKey.STRIPE_API_KEY.value: context.get_env_var(EnvVarKey.STRIPE_API_KEY)}
        api_factory.add_api('stripe_webhook', {ApiMethod.POST: AuthorizationType.PUBLIC}, stripe_env_vars)

    @property
    def rest_api(self):
        return self._rest_api
