from aws_cdk import core
from aws_cdk import aws_lambda
from aws_cdk import aws_apigateway as apigw


class GlobalStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


