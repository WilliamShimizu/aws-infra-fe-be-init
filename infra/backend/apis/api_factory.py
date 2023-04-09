from enum import Enum
from typing import Dict

from aws_cdk import aws_lambda
from aws_cdk import core
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_apigateway as apigw

from backend.cognito.user_pool import CognitoContainer


class AuthorizationType(Enum):
    PUBLIC = 1
    SIGNED_IN = 2
    GROUP_MEMBERSHIP = 3


class ApiMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    CONNECT = 'CONNECT'
    TRACE = 'TRACE'


class ApiFactory(object):

    def __init__(self, scope: core.Construct, stage: str, region: str, cognito_container: CognitoContainer):
        self._scope = scope
        self._region = region
        self._cognito_container = cognito_container
        self._lambda_bucket = self._get_lambda_code_bucket(scope, stage)
        self._rest_api = apigw.RestApi(scope, 'BackendApis')
        self._signed_in_authorizer = None
        self._group_membership_authorizer = None
        self._group_membership_authorizer_lambda = None

    @property
    def rest_api(self):
        return self._rest_api

    def add_api(self, api_name: str, method_to_auth_mapping: Dict[ApiMethod, AuthorizationType],
                environment_variables: Dict[str, str] = None) -> None:
        """
        Creates a lambda and adds it to the api gateway.
        :param api_name: The name of the lambda.
        :param method_to_auth_mapping: A dictionary containing the
        :param environment_variables:
        :return:
        """
        # Create the lambda
        lambda_resource = self._create_lambda(api_name, environment_variables)
        # Add an API to api gateway
        api = self._rest_api.root.add_resource(api_name)
        for api_method, auth_type in method_to_auth_mapping.items():
            kwargs = dict(
                integration=apigw.LambdaIntegration(lambda_resource)
            )
            if auth_type == AuthorizationType.SIGNED_IN:
                kwargs.update(dict(
                    authorization_type=apigw.AuthorizationType.COGNITO,
                    authorizer=apigw.CfnAuthorizer.from_cfn_authorizer(self._get_signed_in_authorizer())
                ))
            elif auth_type == AuthorizationType.GROUP_MEMBERSHIP:
                kwargs.update(dict(
                    authorization_type=apigw.AuthorizationType.CUSTOM,
                    authorizer=apigw.CfnAuthorizer.from_cfn_authorizer(self._get_group_membership_authorizer())
                ))
            # Add a method to our api
            api.add_method(api_method.value, **kwargs)

    def _get_signed_in_authorizer(self):
        if not self._signed_in_authorizer:
            self._signed_in_authorizer = apigw.CfnAuthorizer(
                self._scope, 'CognitoUserPoolAuthorizer',
                name='CognitoUserPoolAuthorizer',
                rest_api_id=self._rest_api.rest_api_id,
                type='COGNITO_USER_POOLS',
                identity_source='method.request.header.Authorization',
                provider_arns=[self._cognito_container.user_pool_arn]
            )
        return self._signed_in_authorizer

    def _get_group_membership_authorizer(self):
        if not self._group_membership_authorizer:
            auth_lambda = self._get_group_membership_authorizer_lambda()
            self._group_membership_authorizer = self.create_custom_authorizer(
                auth_lambda,
                'MembershipAuthorizer',
                type='TOKEN',
                authorizer_result_ttl_in_seconds=core.Duration.days(1).to_seconds(),
                identity_source='method.request.header.Authorization'
            )
        return self._group_membership_authorizer

    def create_custom_authorizer(self, lambda_function: aws_lambda.Function, name: str, **kwargs):
        uri = f'arn:aws:apigateway:{core.Aws.REGION}:lambda:path/2015-03-31/functions/{lambda_function.function_arn}/invocations'
        return apigw.CfnAuthorizer(
            self._scope, name,
            rest_api_id=self._rest_api.rest_api_id,
            authorizer_uri=uri,
            name=name,
            **kwargs
        )

    def _get_group_membership_authorizer_lambda(self):
        if not self._group_membership_authorizer_lambda:
            env_vars = {
                'USER_POOL_ID': self._cognito_container.user_pool.user_pool_id,
                'APP_CLIENT_ID': self._cognito_container.user_pool_client.user_pool_client_id
            }
            self._group_membership_authorizer_lambda = self._create_lambda('membership_auth_lambda', env_vars)
        return self._group_membership_authorizer_lambda

    def _create_lambda(self, name: str, environment_variables: Dict[str, str] = None):
        kwargs = dict(
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='main.handler',
            code=aws_lambda.Code.from_bucket(self._lambda_bucket, name + '.zip')
        )
        if environment_variables:
            kwargs.update(dict(environment=environment_variables))
        return aws_lambda.Function(self._scope, self._get_lambda_function_name(name), **kwargs)

    @staticmethod
    def _get_lambda_code_bucket(scope: core.Construct, stage: str, region: str):
        return s3.Bucket.from_bucket_name(scope, 'LambdaCodeBucket',
                                          bucket_name=f'aws-infra-fe-be-init-lambda-{region}-{stage}')

    @staticmethod
    def _get_lambda_function_name(api_name: str) -> str:
        """
        my_api -> MyApiLambda
        :param api_name:
        :return:
        """
        parts = []
        for part in api_name.split('_'):
            parts.append(part.capitalize())
        parts.append('Lambda')
        return ''.join(parts)
