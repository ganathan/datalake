import json
import os
import boto3

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    print(event)
    return {
        'body': 'SUCCESS',
        'statusCode': 200
    }