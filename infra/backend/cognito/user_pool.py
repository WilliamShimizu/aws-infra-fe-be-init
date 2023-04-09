from aws_cdk import (
    aws_iam as iam,
    aws_cognito as cognito,
    aws_s3 as s3,
    core
)


class CognitoContainer(core.Construct):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        user_data_bucket = s3.Bucket(
            self, "UserData",
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Cognito User Pool
        self._user_pool = cognito.UserPool(self, "UserPool",
            user_pool_name="MyUserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(email_required=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY
        )

        self._user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=self._user_pool
        )

        # Cognito Identity Pool
        self._identity_pool = cognito.CfnIdentityPool(self, "IdentityPool",
            identity_pool_name="IdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                client_id=self._user_pool.user_pool_client_id,
                provider_name=self._user_pool.user_pool_provider_name
            )]
        )

        # IAM role for the Cognito Identity Pool
        self._identity_pool_role = iam.Role(self, "CognitoAuthRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self._identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )

        # Add a policy to the IAM role to allow access to the user's objects in the S3 bucket
        self._identity_pool_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                effect=iam.Effect.ALLOW,
                resources=[f"{user_data_bucket.bucket_arn}/${{cognito-identity.amazonaws.com:sub}}/*"]
            )
        )

        # Attach the IAM role to the Cognito Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self, "IdentityPoolRoleAttachment",
            identity_pool_id=self._identity_pool.ref,
            roles={"authenticated": self._identity_pool_role.role_arn}
        )

        self._paid_subscribers_group = cognito.CfnUserPoolGroup(
            self, "PaidSubscribersGroup",
            user_pool_id=self._user_pool.user_pool_id,
            group_name="paid_subscribers",
            description="Group for paid subscribers"
        )

    @property
    def user_pool(self) -> cognito.UserPool:
        return self._user_pool

    @property
    def user_pool_client(self) -> cognito.UserPoolClient:
        return self._user_pool_client
