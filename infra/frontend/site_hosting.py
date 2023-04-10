from aws_cdk import core, aws_s3 as s3, aws_cloudfront as cloudfront
from aws_cdk import aws_apigateway as apigw

from utils.context import Context
from utils.conventions import get_bucket_name


class SiteHosting(core.Construct):

    def __init__(self, scope: core.Stack, context: Context, rest_api: apigw.RestApi, id: str) -> None:
        super().__init__(scope, id)
        self.scope = scope

        # S3 bucket for the static website
        static_website_bucket = s3.Bucket(scope, 'StaticWebsiteBucket',
            public_read_access=True,
            website_index_document='index.html',
            website_error_document='error.html',
            # ie, aws-infra-fe-be-init-site-[dev|prod]
            bucket_name=get_bucket_name(context, 'site', regional=False)
        )

        # CloudFront Origin Access Identity
        self._origin_access_identity = cloudfront.OriginAccessIdentity(scope, 'CloudFrontOriginAccessIdentity',
            comment='Access S3 bucket content only through CloudFront'
        )

        # Create the CloudFront distribution
        distribution = cloudfront.CloudFrontWebDistribution(
            scope, 'CloudFrontDistribution',
            origin_configs=[
                self._get_static_website_hosting_origin_config(static_website_bucket),
                self._get_api_gateway_origin_config(rest_api),
            ],
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        )

        # Output the CloudFront distribution domain name
        core.CfnOutput(scope, 'DistributionDomainName', value=distribution.domain_name)

    @staticmethod
    def _get_static_website_hosting_origin_config(static_website_bucket: s3.Bucket):
        return cloudfront.SourceConfiguration(
            s3_origin_source=cloudfront.S3OriginConfig(
                s3_bucket_source=static_website_bucket
            ),
            behaviors=[
                cloudfront.Behavior(is_default_behavior=True)
            ],
        )

    def _get_api_gateway_origin_config(self, rest_api: apigw.RestApi):
        return cloudfront.SourceConfiguration(
            custom_origin_source=cloudfront.CustomOriginConfig(
                domain_name=f'{rest_api.rest_api_id}.execute-api.{core.Stack.of(self.scope).region}.amazonaws.com',
                origin_protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
            ),
            behaviors=[cloudfront.Behavior(
                path_pattern='/api/*',
                allowed_methods=cloudfront.CloudFrontAllowedMethods.ALL,
                forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                    query_string=True,
                    headers=['*'],
                    cookies=cloudfront.CfnDistribution.CookiesProperty(forward='all'),
                ),
                compress=True,
            )],
        )
