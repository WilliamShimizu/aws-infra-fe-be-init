import json

from common.shared import get_message


def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': get_message('Public')})
    }


