# --------------------------------------------------------------------------
# Author:       Ganesh Nathan
# Date:         05/08/2020
# Description:  DaaS common lambda to create distribution glue crawler, catalog and table
# --------------------------------------------------------------------------
import copy
import json
import boto3



# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    print('inside init')
    global lambda_client, event_client, glue_client
    glue_client = boto3.client('glue')
    lambda_client = boto3.client('lambda')
    event_client = boto3.client('events')


# -------------------------------------------------
# Check if Crawler exits
# -------------------------------------------------
def crawler_exits(crawler_name):
    try:
        # call the get crawler, if response fails then crawler is not defined
        response = glue_client.get_crawler(
            Name=crawler_name
        )
        return True
    except glue_client.exceptions.EntityNotFoundException:
        return False


# -------------------------------------------------
# Check existence of partition in the Glue Table
# -------------------------------------------------
def partition_exists(glue_db_name, table_name, partition_values):
    try:
        response = glue_client.get_partition(
            DatabaseName=glue_db_name,
            TableName=table_name,
            PartitionValues=partition_values
        )
        return True
    except glue_client.exceptions.EntityNotFoundException:
        return False


# -------------------------------------------------
# Add Partitions to Glue Table
# -------------------------------------------------
def add_table_partitions(glue_db_name, table_name, partitions, partition_values):
    # Check if partition exists already
    if not partition_exists(glue_db_name, table_name, partition_values):
        get_table_response = glue_client.get_table(
            DatabaseName=glue_db_name,
            Name=table_name
        )

        # Extract the existing storage descriptor and Create custom storage descriptor with new partition location
        storage_descriptor = get_table_response['Table']['StorageDescriptor']
        custom_storage_descriptor = copy.deepcopy(storage_descriptor)
        custom_storage_descriptor['Location'] = storage_descriptor['Location'] + partitions + '/'

        print('inside add table partition ' + table_name)
        print(custom_storage_descriptor)
        print(partitions)
        print(partition_values)
        print(glue_db_name)

         # Create partitions in the glue table
        response = glue_client.create_partition(
            DatabaseName=glue_db_name,
            TableName=table_name,
            PartitionInput={
                'Values': partition_values,
                'StorageDescriptor': custom_storage_descriptor
            }
        )
        print(response)
    else:
        print("partition exists...ignoring changes!")


# -------------------------------------------------
# Create new glue crawler
# -------------------------------------------------
def create_crawler(glue_db_name, lakeformation_role_name, crawler_name, domain_name, source_file_path):
    try:
        # call the get crawler, if response fails then crawler is not defined
        response = glue_client.create_crawler(
            Name=crawler_name,
            DatabaseName=glue_db_name,
            Role=lakeformation_role_name,
            Description='Crawler to create catalog on ' + domain_name + ' domain. DaaS Generated!',
            Targets={
                'S3Targets': [
                    {
                        'Path': source_file_path,
                        'Exclusions': [ '*/.raw/*']
                    },
                ]
            },
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'DELETE_FROM_DATABASE'
            },
            Configuration='{ "Version": 1.0, "CrawlerOutput": { "Partitions": { "AddOrUpdateBehavior": "InheritFromTable" } } }',
            Tags={'app-category': 'daas'}
        )
        return response
    except Exception as e:
        print(e)

# -------------------------------------------------
# Create the new glue crawler
# -------------------------------------------------
def start_crawler(crawler_name):
    response = glue_client.start_crawler(
        Name=crawler_name
    )


# -------------------------------------------------
# Create the cloudwatch event for the crawler
# -------------------------------------------------
def create_cloudwatch_event(crawler_name, target_lambda_arn):
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

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    init()
    print(event)
    try:
        glue_db_name = event['glue_db_name']
        lakeformation_role_name = event['lakeformation_role_name']
        target_lambda_name = event['target_lambda_name']
        target_lambda_arn = event['target_lambda_arn']
        crawler_name = event['crawler_name']
        source_file_path = event['source_file_path']
        domain_name = event['domain_name']
        table_name = event['table_name']
        partitions = event['partitions']
        partition_values=event['partition_values']
        if crawler_exits(crawler_name):
            print('1a')
            add_table_partitions(glue_db_name, table_name, partitions, partition_values)
        else:
            print('1b')
            create_crawler(glue_db_name, lakeformation_role_name, crawler_name, domain_name, source_file_path)
            print('1c')
            start_crawler(crawler_name)
            # create_cloudwatch_event(crawler_name, target_lambda_arn)
        return {
            'body': json.dumps('SUCCESS'),
            'statusCode': 200
        }
    except Exception as e:
        print(e)
        return {
            'body': e,
            'statusCode': 400
        }
