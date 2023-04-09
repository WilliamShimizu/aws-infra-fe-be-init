import jwt
import json
import base64
import os
from typing import Dict

# Get the Cognito User Pool information from environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
REGION = os.environ['REGION']
APP_CLIENT_ID = os.environ['APP_CLIENT_ID']

# Construct the JWKs URL using the region and user pool ID
JWKS_URL = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'

# Download the JWKs and cache them
import urllib.request

with urllib.request.urlopen(JWKS_URL) as response:
    JWK_SET = json.loads(response.read())


# Function to get a public key from the JWK Set
def get_public_key(token: str) -> Dict[str, str]:
    jwt_headers = token.split('.')[0]
    jwt_headers_decoded = base64.b64decode(jwt_headers + "===").decode('utf-8')
    jwt_headers_json = json.loads(jwt_headers_decoded)
    kid = jwt_headers_json['kid']

    for key in JWK_SET['keys']:
        if key['kid'] == kid:
            return key
    raise Exception("Public key not found in JWK Set")


def handler(event, context):
    token = event['authorizationToken']
    public_key = get_public_key(token)

    try:
        # Verify and decode the token
        decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience=APP_CLIENT_ID)

        user_groups = decoded_token.get('cognito:groups', [])

        effect = 'Allow' if 'paid_subscribers' in user_groups else 'Deny'

        # Create a policy
        return {
            "principalId": decoded_token['sub'],
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": effect,
                        "Resource": event['methodArn']
                    }
                ]
            }
        }
    except jwt.exceptions.InvalidTokenError as e:
        # If token validation fails, raise an exception
        raise Exception("Unauthorized") from e
