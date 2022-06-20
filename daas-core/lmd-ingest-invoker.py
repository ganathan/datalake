import copy
import json
import os
import urllib.parse
import boto3
import botocore
import csv
from io import StringIO


# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    global s3, s3_client, stpfn_client, lambda_client, event_client, glue_client 
    global daas_config, environment, setup_config_file, id_config_file
    global region, event_converter_stepfn_arn, event_controller_stepfn_arn, s3_core, setup_bucket
    stpfn_client = boto3.client('stepfunctions')
    s3_client = boto3.client('s3')
    s3_core = boto3.client('s3')
    s3 = boto3.resource('s3')
    glue_client = boto3.client('glue')
    lambda_client = boto3.client('lambda')
    event_client = boto3.client('events')
    environment = os.environ["ENV_VAR_ENVIRONMENT"]
    region = os.environ["ENV_VAR_REGION_NAME"]
    daas_config = os.environ["ENV_VAR_DAAS_CONFIG_FILE"]
    event_converter_stepfn_arn = os.environ["ENV_VAR_EVNT_CONVR_STEP_FUNC_ARN"]
    event_controller_stepfn_arn = os.environ["ENV_VAR_EVNT_CONTROL_STEP_FUNC_ARN"]
    setup_bucket = os.environ["ENV_VAR_SETUP_BUCKET"]
    setup_config_file = os.environ["ENV_VAR_SETUP_CONFIG_FILE"]
    id_config_file = os.environ["ENV_VAR_ID_CONFIG_FILE"]

# -------------------------------------------------------------------------------------------
# Read the replication status, database name and database schema  from the daas-config file
# -------------------------------------------------------------------------------------------
def get_client_glue_database_name(data_dict):
    glue_db_name=""
    glue_db_name = data_dict['glue_database']
    return glue_db_name

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


# -------------------------------------------------------------------
# Invoke step function to contol the services deployed on the object
# --------------------------------------------------------------------
def invoke_controller_stepfunction(client_account_id, glue_db_name, params, controller, state_machine_arn):
    try:
        params = {
            'account_id': client_account_id,
            'database_name': glue_db_name,
            'params': params,
            'controller': controller,
            'state_machine_arn': state_machine_arn
        }

        response = stpfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            input= json.dumps(params)
        )
        print(response)
        return response['Payload'].read()
    except Exception as e:
        raise Exception(f'Failed while invoking step function {state_machine_arn}  {params} {e}')

# ---------------------------------------------------------------------
# Invoke step function to converter the object
# ---------------------------------------------------------------------
def invoke_converter_stepfunction(source_bucket, source_key, domain_name, object_name, extension, state_machine_arn):
    try:
        params = {
            'source_bucket': source_bucket,
            'region': region,
            'source_key': source_key,
            'domain_name': domain_name,
            'object_name': object_name,
            'extension': extension
        }

        response = stpfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            input= json.dumps(params)
        )
        return response['Payload'].read()
    except Exception as e:
        raise Exception(f"Failed while invoking step function {state_machine_arn}  {params} {e}")
    

# ---------------------------------------------------------------------
# Get config details from the client s3 bucket
# ---------------------------------------------------------------------        
def get_client_details(source_bucket):
    try:
        s3_indx = source_bucket.find('-s3-')
        client_entity = source_bucket[0:s3_indx]
        config_fileObj = s3_core.get_object(Bucket=setup_bucket, Key=id_config_file)
        data = config_fileObj['Body'].read().decode('utf-8').splitlines()
        records = csv.reader(data)
        headers = next(records)
        client_account_id=''
        for record in records:
            if record[0]==client_entity:
                client_account_id=record[2]
                continue
        setup_fileObj = s3_core.get_object(Bucket=setup_bucket, Key=setup_config_file)
        data = setup_fileObj['Body'].read().decode('utf-8').splitlines()
        records = csv.reader(data)
        headers = next(records)
        database_name=''
        for record in records:
            if record[0]=='gluedb':
                client_database_name=record[1]
        return (client_account_id, client_entity, client_database_name)
    except Exception as e:
        raise ValueError(f"Unable to get config details {e}")
        
        
# ---------------------------------------------------------------------
# Get config details from the client s3 bucket
# ---------------------------------------------------------------------
def get_config_details(source_bucket):
    try:
        replicate=""
        db_name=""
        db_schema=""
        glue_db_name=""
        try:
            s3_client.head_object(Bucket= source_bucket, Key=daas_config)
            fileObj = s3_client.get_object(Bucket= source_bucket, Key=daas_config)
            data_dict = fileObj['Body'].read()
            (replicate, db_name, db_schema) = get_replication_detail(data_dict) 
            glue_db_name = get_client_glue_database_name(data_dict)
        except Exception as e:
            print(f"Config file {daas_config} not defined! Using system defaults!")
        (client_account_id, client_entity, client_database_name) = get_client_details(source_bucket)
        upd_client_entity = client_entity.replace('_','').replace('-','')
        if not glue_db_name:
            glue_db_name=client_database_name + '_' + upd_client_entity + '_' + 'raw'
        else:
            glue_db_name=glue_db_name + '_' + upd_client_entity + '_' + 'raw'
        return (client_account_id, client_entity, replicate, db_name, db_schema, glue_db_name)
    except Exception as e:
        raise Exception('Unable to get config details!  {e}')


# ---------------------------------------------------------------------
# Check if the given key is a file
# ---------------------------------------------------------------------      
def is_file(source_bucket, key, prefix):
    try:
        if (len(prefix) > 2):
            s3_client.head_object(Bucket= source_bucket, Key=key)
            return True
    except Exception as e:
        print(f'key {key} in bucket {source_bucket} is not a valid file!')
        return False


# ---------------------------------------------------------------------
# Get details from the event
# ---------------------------------------------------------------------
def get_object_details(source_bucket, source_key):
    try:
        prefix=source_key.split('/')
        is_object_file = is_file(source_bucket, source_key, prefix)        
        domain_name = source_key.split('/')[0:2][1]  # get the second prefix and assign it as the domain name
        object_name = source_key.split('/')[-1] # get the file name
        short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
        is_dot_folder_object = short_path.rfind('.',0)
        is_ignore_object = short_path.find('-daas-gen-raw')
        is_access_control = object_name.find('access-config.txt')
        return (domain_name, object_name, short_path, is_object_file, is_dot_folder_object, is_ignore_object, is_access_control)
    except Exception as e:
        raise Exception(e)

# ---------------------------------------------------------------------
# Process object to invoke step function
# ---------------------------------------------------------------------
def process_object_metadata(source_bucket, source_key, region, domain_name,controller): 
    try:         
        partition_values=[]
        source_name = source_key.split('/')[0:1][0]  # get the first prefix and assign it as the source name
        partitions = source_key.split('/')[2:-1]  # Remove source name, domain name in the front and the key at the end
        for key in partitions:
            value = key.split('=')[1]
            if value:
                partition_values.append(value)
            else:
                partition_values.append(key)
        path = 's3://' + source_bucket + '/' + source_name + '/' +  domain_name + '/'
        (client_account_id, client_entity, replicate, db_name, db_schema, glue_db_name) = get_config_details(source_bucket)
        crawler_name = client_entity + '-' + source_name + '-' + domain_name + '-' + 'raw-crawler' + '-' + environment
        target_gluejb_lambda_arn = 'arn:aws:lambda:' + region + ':' + client_account_id + ':function:' + client_entity + '-lmd-glujb-sync-generator-' + environment
        glue_admin_role_name= client_entity + '-rle-ingest-glue-controller-admin-' + environment
        table_name = domain_name.replace('-','_')
        data={}
        data['account_id'] = client_account_id
        data['region'] = region
        data['glue_db_name'] = glue_db_name
        data['glue_admin_role_name'] = glue_admin_role_name
        data['gluejb_lambda_arn'] = target_gluejb_lambda_arn
        data['src_bucket_name'] = source_bucket
        data['src_source_name'] = source_name    
        data['source_file_path'] = path
        data['domain_name'] = domain_name
        data['crawler_name'] = crawler_name
        data['table_name'] = table_name
        data['partitions'] = partitions
        data['partition_values'] = partition_values
        data['replicate'] = replicate
        data['db_name'] = db_name
        data['db_schema'] = db_schema    
        params=json.dumps(data)
        
        resp = invoke_controller_stepfunction(client_account_id, glue_db_name, params, controller, state_machine_arn=event_controller_stepfn_arn)
        return resp
    except Exception as e:
        raise Exception(e)
        
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
                region = record['awsRegion']
                (domain_name, object_name, short_path, is_object_file, is_dot_folder_object, is_ignore_object, is_access_control) = get_object_details(source_bucket, source_key)
                if is_dot_folder_object != -1 and is_access_control != -1:
                    controller = 'access-control'
                    (client_account_id, client_entity, replicate, db_name, db_schema, glue_db_name) = get_config_details(source_bucket)
                    fileObj = s3_client.get_object(Bucket= source_bucket, Key=source_key)
                    params = fileObj['Body'].read().decode('utf-8').splitlines()
                    resp = invoke_controller_stepfunction(client_account_id, glue_db_name, params, controller, state_machine_arn=event_controller_stepfn_arn)
                elif is_object_file and object_name and is_dot_folder_object == -1 and is_ignore_object == -1:
                    extension = object_name.split('.')[-1].lower() # get the file extension.
                    if extension == 'xml' or extension == 'xls' or extension == 'xlsx' or extension == 'md':
                        resp = invoke_converter_stepfunction(source_bucket, source_key, domain_name, object_name, extension, state_machine_arn=event_converter_stepfn_arn)
                    else:
                        controller = 'metadata-generate'
                        resp = process_object_metadata(source_bucket, source_key, region, domain_name,controller)
                else:
                    if is_dot_folder_object != -1 or is_ignore_object != -1:
                        resp= source_bucket +  '/' + source_key + ' is not a valid file.. processing ignored!'
                    else:
                        resp=source_bucket +  '/' + source_key + ' is not a valid file to process. Please ensure files are nested with data source and dataset prefix...  processing ignored!'
            return {
                'body': resp,
                'statusCode': 200
            }
        except Exception as e:
            return {
                'body': json.loads(json.dumps(e, default=str)),
                'statusCode': 400
            }
