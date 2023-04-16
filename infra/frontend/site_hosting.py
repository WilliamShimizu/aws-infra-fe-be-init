from typing import List

from aws_cdk import core, aws_s3 as s3, aws_cloudfront as cloudfront
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_route53 as r53
from aws_cdk import aws_certificatemanager as acm

from backend.backend_apis import BackendApiLayer
from utils.context import Context
from utils.conventions import get_bucket_name, DOMAIN_NAME


class NetworkingLayer(core.Construct):

    def __init__(self, scope: core.Stack, context: Context, rest_api: BackendApiLayer, id: str) -> None:
        super().__init__(scope, id)
        self._context = context

        # S3 bucket for the static website
        static_website_bucket = s3.Bucket(scope, 'StaticWebsiteBucket',
            public_read_access=True,
            website_index_document='index.html',
            website_error_document='error.html',
            removal_policy=core.RemovalPolicy.DESTROY,
            # ie, aws-infra-fe-be-init-site-[dev|prod]
            bucket_name=get_bucket_name(context, 'site')
        )

        # CloudFront Origin Access Identity
        self._origin_access_identity = cloudfront.OriginAccessIdentity(scope, 'CloudFrontOriginAccessIdentity',
            comment='Access S3 bucket content only through CloudFront'
        )

        if context.stage == 'prod':
            # If you already have a hosted zone in your aws account, use this.
            # hosted_zone = aws_route53.HostedZone.from_lookup(
            #     self, "HostedZone",
            #     domain_name=DOMAIN_NAME  # Replace with your custom domain name
            # )

            hosted_zone = r53.HostedZone(
                scope, "HostedZone",
                zone_name=DOMAIN_NAME
            )

            # Request a certificate for your domain and its subdomains
            certificate = acm.DnsValidatedCertificate(
                self,
                "SiteCertificate",
                domain_name=DOMAIN_NAME,
                subject_alternative_names=[f"*.{DOMAIN_NAME}"],
                hosted_zone=hosted_zone,
                region="us-east-1",  # CloudFront requires ACM certificates to be in the us-east-1 region
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
                cloudfront.Behavior(
                    is_default_behavior=True,  # Important, we want all non /api/* traffic to go here.
                )
            ],
        )

    @staticmethod
    def _get_api_gateway_origin_config(backend_api: BackendApiLayer):
        return cloudfront.SourceConfiguration(
            custom_origin_source=cloudfront.CustomOriginConfig(
                domain_name=backend_api.domain_name,
                origin_protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
            ),
            behaviors=[cloudfront.Behavior(
                path_pattern='/api/*',
                allowed_methods=cloudfront.CloudFrontAllowedMethods.ALL,
                forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                    query_string=True,
                    headers=['*'],
                ),
                compress=True,
            )],
        )
