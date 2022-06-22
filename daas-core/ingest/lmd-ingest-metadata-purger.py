# ----------------------------------------------------------------------------------------------
# Author:       Ganesh Nathan
# Date:         06/12/2022
# Description:  DaaS common lambda to clean up the crawler, glue table and cloudwatch event.
# ----------------------------------------------------------------------------------------------
import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -------------------------------------------------
# Check if Glue Crawler exits
# -------------------------------------------------
def crawler_exists(glue_client, crawler_name):
    try:
        # call the get crawler, if response fails then crawler is not defined
        response = glue_client.get_crawler(
            Name=crawler_name
        )
        return True
    except glue_client.exceptions.EntityNotFoundException:
        print(f"crawler {crawler_name} does not exist... ignoring!")
        return False

# -------------------------------------------------
# Check if Glue Table exits
# -------------------------------------------------
def table_exists(glue_client, glue_db_name, dataset):
    try:
        # call the get table, if response fails then table is not defined
        response = glue_client.get_table(
            DatabaseName=glue_db_name,
            Name=dataset
        )
        return True
    except glue_client.exceptions.EntityNotFoundException:
        print(f"table {dataset} does not exist... ignoring!")
        return False
        
# -------------------------------------------------
# Drop the Glue Table
# -------------------------------------------------
def drop_table(glue_client, glue_db_name, dataset):
    try:
        response = glue_client.delete_table(
            DatabaseName=glue_db_name,
            Name=dataset
        )
        logger.info(f'removed table {dataset} in database {glue_db_name}')
        return response
    except glue_client.exceptions.EntityNotFoundException:
        response = f"table {dataset} does not exist {glue_db_name} in database... ignoring!"
        return response


# -------------------------------------------------
# Delete the glue crawler
# -------------------------------------------------
def remove_crawler(glue_client, crawler_name):
    try:
        response = glue_client.delete_crawler(
            Name=crawler_name
        )
        logger.info(f'removed crawler {crawler_name}')
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
def get_glue_client(region,target_glue_service_role_arn):
    try:
        url='https://sts.' + region + '.amazonaws.com/'
        sts_connection = boto3.client('sts', region_name=region, endpoint_url=url)
        
        daas_client = sts_connection.assume_role(
            RoleArn=target_glue_service_role_arn,
            RoleSessionName="daas-core"
        )
        ACCESS_KEY = daas_client['Credentials']['AccessKeyId']
        SECRET_KEY = daas_client['Credentials']['SecretAccessKey']
        SESSION_TOKEN = daas_client['Credentials']['SessionToken']
        glue_client = boto3.client('glue', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)
        return glue_client
    except Exception as e:
        raise Exception(f'Unable to assume role {target_glue_service_role_arn}! {e}')

    
    
# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    print(event)
    try:
        environment = os.environ["ENV_VAR_ENVIRONMENT"]
        account_id = event['account_id']
        region = event['region']
        params = json.loads(event['params'])
        client_account_id = params['account_id']
        client_entity = params['entity']
        glue_db_name = params['glue_db_name']
        glue_admin_role_name = params['glue_admin_role_name']
        table_name = params['table_name']
        commands = params['commands']
        for command in commands:
            try:
                datasource = command.split('/')[0]
                dataset = command.split('/')[1]
                crawler_name = client_entity + '-' + datasource + '-' + dataset + '-' + 'raw-crawler' + '-' + environment
                event_name = crawler_name
                target_glue_service_role_arn='arn:aws:iam::' + client_account_id + ':role/' + glue_admin_role_name
                glue_client = get_glue_client(region, target_glue_service_role_arn)
                logger.info(f'processing carwler {crawler_name}')
                if crawler_exists(glue_client, crawler_name):
                    resp = remove_crawler(glue_client, crawler_name)
                logger.info(f'processing table {dataset}')
                if table_exists(glue_client, glue_db_name, dataset):
                    resp = drop_table(glue_client, glue_db_name, dataset)
                    resp = delete_cloudwatch_event(glue_client, event_name)
                else:
                    resp = f"Unable to find crawler {crawler_name} ignoring!"
            except Exception as e:
                resp = f'Got an exception {e}'
        return {
            'body': resp,
            'statusCode': 200
        }
    except Exception as e:
        return {
            'body': json.loads(json.dumps(e, default=str)),
            'statusCode': 400
        }
