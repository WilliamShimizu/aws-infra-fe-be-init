from aws_cdk import (
    aws_iam as iam,
    aws_cognito as cognito,
    aws_s3 as s3,
    core
)

from utils.context import Context
from utils.conventions import get_bucket_name, get_resource_name


class CognitoContainer(core.Construct):

    def __init__(self, scope: core.Stack, id: str, context: Context) -> None:
        super().__init__(scope, id)

        user_data_bucket = s3.Bucket(
            scope, 'UserData',
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY,
            bucket_name=get_bucket_name(context, 'user-data')
        )

        # Cognito User Pool
        self._user_pool = cognito.UserPool(scope, 'UserPool',
            user_pool_name=get_resource_name('UserPool'),
            self_sign_up_enabled=True,
            removal_policy=core.RemovalPolicy.DESTROY,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(**self._build_standard_attributes()),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY
        )

        self._user_pool_client = cognito.UserPoolClient(
            scope, 'UserPoolClient',
            user_pool=self._user_pool
        )

        # Cognito Identity Pool
        self._identity_pool = cognito.CfnIdentityPool(scope, 'IdentityPool',
            identity_pool_name=get_resource_name('IdentityPool'),
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                client_id=self._user_pool_client.user_pool_client_id,
                provider_name=self._user_pool.user_pool_provider_name
            )]
        )

        # IAM role for the Cognito Identity Pool
        self._identity_pool_role = iam.Role(scope, 'CognitoAuthRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                conditions={
                    'StringEquals': {
                        'cognito-identity.amazonaws.com:aud': self._identity_pool.ref
                    },
                    'ForAnyValue:StringLike': {
                        'cognito-identity.amazonaws.com:amr': 'authenticated'
                    }
                },
                assume_role_action='sts:AssumeRoleWithWebIdentity'
            )
        )

        # Add a policy to the IAM role to allow access to the user's objects in the S3 bucket
        self._identity_pool_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    's3:GetObject',
                    's3:PutObject',
                    's3:DeleteObject'
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'{user_data_bucket.bucket_arn}/${{cognito-identity.amazonaws.com:sub}}/*']
            )
        )

        # Attach the IAM role to the Cognito Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            scope, 'IdentityPoolRoleAttachment',
            identity_pool_id=self._identity_pool.ref,
            roles={'authenticated': self._identity_pool_role.role_arn}
        )

        self._paid_subscribers_group = cognito.CfnUserPoolGroup(
            scope, 'PaidSubscribersGroup',
            user_pool_id=self._user_pool.user_pool_id,
            group_name='paid_subscribers',
            description='Group for paid subscribers'
        )

    @staticmethod
    def _build_standard_attributes() -> dict:
        return dict(
            email=cognito.StandardAttribute(required=True, mutable=True),
            preferred_username=cognito.StandardAttribute(required=False, mutable=False)
        )

    @property
    def user_pool(self) -> cognito.UserPool:
        return self._user_pool

    @property
    def user_pool_client(self) -> cognito.UserPoolClient:
        return self._user_pool_client
