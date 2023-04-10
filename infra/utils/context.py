from enum import Enum
from typing import Dict
from aws_cdk.core import Environment


class EnvVarKey(Enum):
    STRIPE_API_KEY = 'stripeApiKey'
    STRIPE_ENDPOINT = 'stripeEndpoint'


class Context(object):

    def __init__(self, project_name: str, environment: Environment, stage: str, env_vars: Dict[EnvVarKey, str]):
        self._project_name = project_name
        self._env = environment
        self._stage = stage
        self._env_vars = env_vars

    @property
    def project_name(self) -> str:
        return self._project_name

    @property
    def region(self) -> str:
        return self._env.region

    @property
    def stage(self) -> str:
        return self._stage

    def get_env_var(self, key: EnvVarKey) -> str:
        return self._env_vars[key]

    @property
    def get_environment(self) -> Environment:
        return self._env
