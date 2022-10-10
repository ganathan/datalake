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
# Read the subnets within the given vpc and filter by tag and key
# -------------------------------------------------------------------------------------------
def get_subnets(vpc_id,tag_key,tag_value):
    response = ec2_client.describe_subnets(Filters=[
        {
            "Name":"vpc-id",
            "Values":[vpc_id]
        },
        {
            "Name":"tag:"+tag_key,
            "Values":[tag_value]
        }
    ]) 
    subnets = list(map(lambda s: s["SubnetId"],response["Subnets"]))
    subnet_result= json.dumps(subnets,indent=2)
    logger.info(f'{subnet_result}')

    # "set" removes dupiicates from availability zones list
    avaiability_zones = list(set((map(lambda s: s["AvailabilityZone"],response["Subnets"]))))
    az_result = json.dumps(avaiability_zones,indent=2)
    logger.info(f'{az_result}')

    return {
        "Subnets":subnets,
        "AvailabilityZones":avaiability_zones
    }

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
        response = get_subnets(props["VpcId"],props["TagKey"],props["TagValue"])
        send(event, context, SUCCESS, response)
    except Exception as e:
        logger.error(f'{e}')
        send(event, context, FAILED, {})
