import json
import boto3

# -------------------------------------------------
# Create the cloudwatch event for the crawler
# -------------------------------------------------
def create_cloudwatch_event(crawler_name):
    rule_name = crawler_name + "-event"
    event_json_string = json.dumps({'source': ['aws.glue'], 'detail-type': ['Glue Crawler State Change'],
                                    'detail': {'crawlerName': [crawler_name], 'state': ['Succeeded']}})
 
    # Create the rule first
    rule_response = event_client.put_rule(
        Name=rule_name,
        EventPattern=event_json_string,
        State='ENABLED',
        Description='Cloud Watch event rule for crawler ' + crawler_name
    )
 
    # Place the lambda target for the rule
    response = event_client.put_targets(
        Rule=rule_name,
        Targets=[{'Id': rule_name, 'Arn': target_lambda_arn}, ]
    )
 
    # Grant invoke permission to Lambda
    lambda_client.add_permission(
        FunctionName=target_lambda_name,
        StatementId=rule_name,
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn=rule_response['RuleArn'],
    )



# ----------------------------------------------------------
# Invoke metadata generator lambda on the client account
# ----------------------------------------------------------
def invoke_lambda(glue_db_name, lakeformation_role_name, target_lambda_name, target_lambda_arn, target_lambda_role_arn, crawler_name, path, domain_name, table_name, partitions, partition_values):
    sts_connection = boto3.client('sts')
    daas_client = sts_connection.assume_role(
        RoleArn=target_lambda_role_arn,
        RoleSessionName="daas-core"
    )
    ACCESS_KEY = daas_client['Credentials']['AccessKeyId']
    SECRET_KEY = daas_client['Credentials']['SecretAccessKey']
    SESSION_TOKEN = daas_client['Credentials']['SessionToken']
    lambda_client = boto3.client('lambda', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)
    data={}
    data['glue_db_name'] = glue_db_name
    data['lakeformation_role_name'] = lakeformation_role_name
    data['target_lambda_name'] = target_lambda_name
    data['target_lambda_arn'] = target_lambda_arn
    data['source_file_path'] = path
    data['domain_name'] = domain_name
    data['crawler_name'] = crawler_name
    data['table_name'] = table_name
    data['partitions'] = partitions
    data['partition_values'] = partition_values
    json_str=json.dumps(data)
    response = lambda_client.invoke(
        FunctionName= target_lambda_arn, 
        InvocationType = "Event", 
        Payload = json_str
    )
    return response['Payload'].read()

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    print(f'event is {event}')
    try:
        glue_db_name = event['glue_db_name']
        lakeformation_role_name = event['lakeformation_role_name']
        target_lambda_name = event['target_lambda_name']
        target_lambda_arn = event['target_lambda_arn']
        target_lambda_role_arn = event['target_lambda_role_arn']
        crawler_name = event['crawler_name']
        path = event['path']
        domain_name = event['domain_name']
        table_name = event['table_name']
        partitions = event['partitions']
        partition_values = event['partition_values']
        result = invoke_lambda(glue_db_name, lakeformation_role_name, target_lambda_name, target_lambda_arn, target_lambda_role_arn, crawler_name, path, domain_name, table_name, partitions, partition_values)
        # create_cloudwatch_event(crawler_name)
        print(result)
        return {
            'body': 'SUCCESS',
            'statusCode': 200
        }
    except Exception as e:
        print(e)
        return {
            'body': json.dumps(e),
            'statusCode': 400
        }

