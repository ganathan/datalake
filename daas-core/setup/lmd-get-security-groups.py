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
    global ec2_client, SUCCESS, FAILED
    ec2_client = boto3.client('ec2')
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# -------------------------------------------------------------------------------------------
# Read the security groups within the given vpc and filter by tag and key
# -------------------------------------------------------------------------------------------
def get_security_groups(vpc_id,tag_key,tag_value):
    response = ec2_client.describe_security_groups(Filters=[
        {
            "Name":"vpc-id",
            "Values":[vpc_id]
        },
        {
            "Name":"tag:"+tag_key,
            "Values":[tag_value]
        }
    ]) 
    result = list(map(lambda s: s["GroupId"],response["SecurityGroups"]))
    json_result= json.dumps(result,indent=2)
    logger.info(f'{json_result}')
    return result

# -------------------------------------------------------------------------------------------
# Send response to the invoker with security group details
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
        response = get_security_groups(props["VpcId"],props["TagKey"],props["TagValue"])
        send(event, context, SUCCESS, 
        {
            "SecurityGroups":response
        })
    except Exception as e:
        logger.error(f'{e}')
        send(event, context, FAILED, {})
