import json
import boto3
import uuid

client = boto3.client('stepfunctions')
    
# ---------------------------------------------------------
# Get bucket details from SQS message
# ----------------------------------------------------------
def get_file_details(s3_event_body):
    try:
        for event in s3_event_body['Records']:
            bucket_name = event['s3']['bucket']['name']
            file_key    = event['s3']['object']['key']
            file_key_details = file_key.split('/')[-1]
            file_type  = file_key_details.split('.')[-1]
        return bucket_name, file_key, file_type
    except:
        print(f'cannot retrieve file details from S3/SQS Event: {s3_event_body}')
        return None, None, None
        
def invoke_stepfunction(result):
    response = client.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:760160142816:stateMachine:hamsa-sf-us-east-1-event-processor-pipeline',
        input= json.dumps(result)
    )

# --------------------------------------------------------------
# Main lambda function to read sqs message and get file_type
# --------------------------------------------------------------
def lambda_handler(event, context):
    print(f'event from sqs is {event}')
    if len(event['Records']) >= 1:
        try:
            for record in event['Records']:
                s3_event_body = json.loads(record['body'])
                bucket_name, file_key, file_type = get_file_details(s3_event_body)
                if get_file_details(s3_event_body):
                    result = {
                        'bucket_name': bucket_name,
                        'file_key': file_key,
                        'file_type': file_type
                    }
                    print(bucket_name, file_key, file_type)
                    print(result)
                    invoke_stepfunction(result)
                else:
                    print('bucket_name, file_key, file_type are not parsed properly')
        except Exception as error:
            print(error)
            