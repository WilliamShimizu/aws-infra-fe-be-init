import sys
import os

# Add the path to the shared code directory to sys.path
common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if common_path not in sys.path:
    sys.path.append(common_path)

from common.shared import get_message


def handler(event, context):
    return get_message('Singed In')


