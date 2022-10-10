import boto3
import os
import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    logger.info(event)

    try:
        resp="Success!"
        return {
            'body': resp,
            'statusCode': 200
        }
    except Exception as e:
        return {
            'body': json.loads(json.dumps(e, default=str)),
            'statusCode': 400
        }
