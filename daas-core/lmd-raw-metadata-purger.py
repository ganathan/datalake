# ----------------------------------------------------------------------------------------------
# Author:       Ganesh Nathan
# Date:         06/12/2022
# Description:  DaaS common lambda to clean up the crawler, glue table and cloudwatch event.
# ----------------------------------------------------------------------------------------------
import json
import boto3
    

# -------------------------------------------------
# Check if Crawler exits
# -------------------------------------------------
def crawler_exits(glue_client, crawler_name):
    try:
        # call the get crawler, if response fails then crawler is not defined
        response = glue_client.get_crawler(
            Name=crawler_name
        )
        return True
    except glue_client.exceptions.EntityNotFoundException:
        print(f"crawler %s does not exist... ignoring!' %(crawler_name)")
        return False


# -------------------------------------------------
# Drop the Glue Table
# -------------------------------------------------
def drop_table(glue_client, glue_db_name, table_name, partition_values):
    try:
        response = glue_client.delete_table(
            DatabaseName=glue_db_name,
            TableName=table_name
        )   
        return response
    except glue_client.exceptions.EntityNotFoundException:
        response = f"table %s does not exist %s in database... ignoring!' %(table_name, glue_db_name)"
        return response


# -------------------------------------------------
# Delete the glue crawler
# -------------------------------------------------
def remove_crawler(glue_client, crawler_name):
    try:
        response = glue_client.delete_crawler(
            Name=crawler_name
        )
        return response
    except Exception as e:
        return f'Unable to remove crawler {e}'


# -------------------------------------------------
# Create the cloudwatch event for the crawler
# -------------------------------------------------
def delete_cloudwatch_event(glue_client, rule_name):
    event_client = boto3.client('events')
    try:
        # Remove the target from the rule
        response = event_client.remove_targets(
            Rule=rule_name,
            Ids=[rule_name]
        )

        # Delete event rule
        response = event_client.delete_rule(
            Name=rule_name
        )
        return response
    except Exception as e:
        return f'Unable to detele cloudwatch event {e}'

# -------------------------------------------------
# get the glue daas client
# -------------------------------------------------
def get_glue_client(target_glue_service_role_arn):
    sts_connection = boto3.client('sts')
    print('assuming role..... ' + target_glue_service_role_arn)
    
    daas_client = sts_connection.assume_role(
        RoleArn=target_glue_service_role_arn,
        RoleSessionName="daas-core"
    )
    ACCESS_KEY = daas_client['Credentials']['AccessKeyId']
    SECRET_KEY = daas_client['Credentials']['SecretAccessKey']
    SESSION_TOKEN = daas_client['Credentials']['SessionToken']
    glue_client = boto3.client('glue', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)
    print('got the glue_client')
    return glue_client
    
    
# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    print(event)
    try:
        params = json.loads(event['params'])
        client_account_id = params['account_id']
        glue_db_name = params['glue_db_name']
        glue_admin_role_name = params['glue_admin_role_name']
        crawler_name = params['crawler_name']
        table_name = params['table_name']
        event_name = crawler_name
        target_glue_service_role_arn='arn:aws:iam::' + client_account_id + ':role/' + glue_admin_role_name
        print(target_glue_service_role_arn)
        glue_client = get_glue_client(target_glue_service_role_arn)
        if crawler_exits(glue_client, crawler_name):
            print('1a')
            resp = remove_crawler(glue_client, crawler_name)
            resp = drop_table(glue_client, glue_db_name, table_name)
            resp = delete_cloudwatch_event(glue_client, event_name)
        return {
            'body': resp,
            'statusCode': 200
        }
    except Exception as e:
        return {
            'body': json.loads(json.dumps(e, default=str)),
            'statusCode': 400
        }
