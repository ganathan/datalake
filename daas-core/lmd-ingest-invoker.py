import copy
import json
import os
import urllib.parse
import boto3
import hashlib
from io import StringIO


# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    global s3, s3_client, stpfn_client, lambda_client, event_client, glue_client, glue_db_name 
    global lakeformation_role_name, target_lambda_name, daas_config, accountid, environment
    global region, event_converter_stepfn_arn
    stpfn_client = boto3.client('stepfunctions')
    s3_client = boto3.client('s3')
    s3 = boto3.resource('s3')
    glue_client = boto3.client('glue')
    lambda_client = boto3.client('lambda')
    event_client = boto3.client('events')
    accountid = os.environ["ENV_VAR_ACCOUNT_ID"]
    environment = os.environ["ENV_VAR_ENVIRONMENT"]
    region = os.environ["ENV_VAR_REGION_NAME"]
    daas_config = os.environ["ENV_VAR_DAAS_CONFIG_FILE"]
    glue_db_name = os.environ["ENV_VAR_DAAS_CORE_GLUE_DB"]
    lakeformation_role_name = os.environ["ENV_VAR_GLUE_SERVICE_ROLE"]
    target_lambda_name = os.environ["ENV_VAR_CLIENT_LAMBDA_NAME"]
    event_converter_stepfn_arn = os.environ["ENV_VAR_EVNT_CONVR_STEP_FUNC_ARN"]


# ----------------------------------------------------------
# Read the account id from the daas-config file
# ----------------------------------------------------------
def get_client_accountid(data_dict):
    accountid = json.loads(data_dict)['account_id']
    return accountid

# ----------------------------------------------------------
# Read the region from the daas-config file
# ----------------------------------------------------------
def get_client_region(data_dict):
    region = json.loads(data_dict)['region']
    return region

# ----------------------------------------------------------
# Read the entity from the daas-config file
# ----------------------------------------------------------
def get_client_entity_name(data_dict):
    entity_name = json.loads(data_dict)['entity']
    return entity_name

# -------------------------------------------------------------------------------------------
# Read the replication status, database name and database schema  from the daas-config file
# -------------------------------------------------------------------------------------------
def get_replication_detail(data_dict):
    replicate = json.loads(data_dict)['replicate']
    db_name=""
    db_schema=""
    if replicate:
        db_name = json.loads(data_dict)['repl_db_info']['db_name']
        db_schema = json.loads(data_dict)['repl_db_info']['db_schema']
    return replicate, db_name, db_schema 

# ----------------------------------------------------------
# Invoke metadata generator lambda on the client account
# ----------------------------------------------------------
def invoke_lambda(target_lambda_arn, target_gluejb_lambda_arn, source_bucket, source_name, target_lambda_role_arn, crawler_name, 
                path, domain_name, table_name, value, partition_values, replicate, db_name, db_schema):
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
    data['gluejb_lambda_arn'] = target_gluejb_lambda_arn
    data['src_bucket_name'] = source_bucket
    data['src_source_name'] = source_name
    data['source_file_path'] = path
    data['domain_name'] = domain_name
    data['crawler_name'] = crawler_name
    data['table_name'] = table_name
    data['partitions'] = value
    data['partition_values'] = partition_values
    data['replicate'] = replicate
    data['db_name'] = db_name
    data['db_schema'] = db_schema
    json_str=json.dumps(data)
    response = lambda_client.invoke(
        FunctionName= target_lambda_arn, 
        InvocationType = "Event", 
        Payload = json_str
    )
    return response['Payload'].read()

# ----------------------------------------------------------
# Invoke step function to convert the object
# ----------------------------------------------------------
def invoke_stepfunction(source_bucket, source_key, domain_name, object_name, extension):
    params = {
        'source_bucket': source_bucket,
        'source_key': source_key,
        'domain_name': domain_name,
        'object_name': object_name,
        'extension': extension
    }

    response = stpfn_client.start_execution(
        stateMachineArn=event_converter_stepfn_arn,
        input= json.dumps(params)
    )
    return response['Payload'].read()

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    init()
    print(event)
    if len(event['Records']) >= 1:
        try:
            for record in json.loads(event['Records'][0]['body'])['Records']:
                source_bucket = record['s3']['bucket']['name']
                source_key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
                domain_name = source_key.split('/')[0:2][1]  # get the second prefix and assign it as the domain name
                object_name = source_key.split('/')[-1] # get the file name
                short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
                is_dot_folder_object = short_path.rfind('.',0)
                is_ignore_object = short_path.find('-daas-gen-raw')
                if object_name and is_dot_folder_object == -1 and is_ignore_object == -1:
                    extension = object_name.split('.')[-1].lower() # get the file extension.
                    if extension == 'xml' or extension == 'xls' or extension == 'xlsx':
                        invoke_stepfunction(source_bucket, source_key, domain_name, object_name, extension)
                    else:                   
                        partition_values=[]
                        source_name = source_key.split('/')[0:1][0]  # get the first prefix and assign it as the source name
                        partitions = source_key.split('/')[2:-1]  # Remove source name, domain name in the front and the key at the end
                        for key in partitions:
                            value = key.split('=')[1]
                            print(value)
                            if value:
                                partition_values.append(value)
                            else:
                                partition_values.append(key)
                        path = 's3://' + source_bucket + '/' + source_name + '/' +  domain_name + '/'
                        fileObj = s3_client.get_object(Bucket= source_bucket, Key=daas_config)
                        data_dict = fileObj['Body'].read()
                        account_id = get_client_accountid(data_dict)
                        region = get_client_region(data_dict)
                        entity = get_client_entity_name(data_dict)
                        (replicate, db_name, db_schema) = get_replication_detail(data_dict)
                        target_lambda_arn = 'arn:aws:lambda:' + region + ':' + account_id + ':function:' + target_lambda_name
                        target_lambda_role_arn = 'arn:aws:iam::' + account_id + ':role/rle-' + target_lambda_name
                        crawler_name = entity + '-' + source_name + '-' + domain_name + '-' + 'raw-crawler'
                        target_gluejb_lambda_arn = 'arn:aws:lambda:' + region + ':' + account_id + ':function:' + entity + '-lmd-glujb-sync-generator-' + environment
                        table_name = domain_name.replace('-','_')
                        result = invoke_lambda(target_lambda_arn, target_gluejb_lambda_arn, source_bucket, source_name, target_lambda_role_arn, crawler_name, path, 
                                     domain_name, table_name, partitions, partition_values, replicate, db_name, db_schema)
                        # create_cloudwatch_event(crawler_name)
                        print(result)
                else:
                    print(source_key + " processing ignored!")
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
