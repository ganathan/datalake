import boto3
import json
import logging
import os
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    global org_client, SUCCESS, FAILED
    org_client = boto3.client('organizations')
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# -------------------------------------------------------------------------------------------
# Read the organizations within the account
# -------------------------------------------------------------------------------------------
def get_orgs():
    orgs = org_client.describe_organization() 
    orgs_result= json.dumps(orgs,indent=2)
    logger.info(f'{orgs_result}')
    return orgs

# -------------------------------------------------------------------------------------------
# Send response to the invoker with subnet details
# -------------------------------------------------------------------------------------------
def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']
    logger.info(f'{responseUrl}')
    responseBody = {
        'Status' : responseStatus,
        'Reason' : reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
        'PhysicalResourceId' : physicalResourceId or context.log_stream_name,
        'StackId' : event['StackId'],
        'RequestId' : event['RequestId'],
        'LogicalResourceId' : event['LogicalResourceId'],
        'NoEcho' : noEcho,
        'Data' : responseData
    }
    json_responseBody = json.dumps(responseBody)
    logger.info(json_responseBody)
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }
    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        logger.info("Status code:", response.status)
    except Exception as e:
        logger.info(f'{e} send(..) failed executing http.request(..):')


# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    init()
    json_event = json.dumps(event)
    logger.info(f'{json_event}')
    props = event['ResourceProperties']
    try:
        response = get_orgs()
        send(event, context, SUCCESS, 
        {
            "Arn":response["Organization"]["Arn"]
        },response["Organization"]["Id"])
    except Exception as e:
        logger.error(f'{e}')
        send(event, context, FAILED, {})
