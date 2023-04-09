import json
import boto3
import os
import stripe

# Set your Stripe API key
stripe.api_key = os.environ['STRIPE_API_KEY']

cognito = boto3.client('cognito-idp')
user_pool_id = os.environ['COGNITO_USER_POOL_ID']
stripe_endpoint = os.environ['STRIPE_ENDPOINT']
group_name = "paid_subscribers"


def lambda_handler(event, context):
    # Parse the webhook payload

    stripe_event: stripe.Event = None
    try:
        stripe_event = get_stripe_event(event)
    except Exception as e:
        # TODO: log exception.
        return {
            'statusCode': 400,
            'body': 'Invalid Payload'
        }

    possibly_buying = stripe_event["type"] in {'customer.subscription.created', 'customer.subscription.updated'}
    status_is_acceptable = stripe_event['status'] in {'active', 'trialing'}
    customer_id = stripe_event["data"]["object"]["customer"]
    if possibly_buying and status_is_acceptable:
        add_user_to_group(customer_id)
    else:
        remove_user_from_group(customer_id)
    return {'statusCode': 200, 'body': 'Success'}


def get_stripe_event(event) -> stripe.Event:
    stripe_signature = event['headers']['Stripe-Signature']
    payload = event['body']
    return stripe.Webhook.construct_event(payload, stripe_signature, stripe_endpoint)


def add_user_to_group(customer_id):
    user = get_user_by_stripe_customer_id(customer_id)
    cognito.admin_add_user_to_group(
        UserPoolId=user_pool_id,
        Username=user['Username'],
        GroupName=group_name
    )


def remove_user_from_group(customer_id):
    user = get_user_by_stripe_customer_id(customer_id)
    cognito.admin_remove_user_from_group(
        UserPoolId=user_pool_id,
        Username=user['Username'],
        GroupName=group_name
    )


def get_user_by_stripe_customer_id(customer_id):
    # Retrieve the customer object from Stripe
    customer = stripe.Customer.retrieve(customer_id)
    cognito_username = customer.metadata['cognito_username']

    response = cognito.list_users(
        UserPoolId=user_pool_id,
        Filter=f"username = \"{cognito_username}\""
    )
    if response['Users']:
        return response['Users'][0]
    raise ValueError(f'Unable to find user with user name {cognito_username} from stripe customer {customer_id}!')
