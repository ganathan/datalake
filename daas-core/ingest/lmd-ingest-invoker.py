import copy
import json
import os
import urllib.parse
import boto3
import botocore
import csv
import logging
from io import StringIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
def invoke_controller_stepfunction(client_account_id, glue_db_name, region, params, controller, state_machine_arn):
    try:
        params = {
            'account_id': client_account_id,
            'database_name': glue_db_name,
            'region': region,
            'params': params,
            'controller': controller,
            'state_machine_arn': state_machine_arn
        }

        response = stpfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            input= json.dumps(params)
        )
        return f'Step function {state_machine_arn} started!'
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
        return f'Step function {state_machine_arn} started!'
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
            logger.info(f"Config file {daas_config} not defined! Using system defaults!")
        (client_account_id, client_entity, client_database_name) = get_client_details(source_bucket)
        upd_client_entity = client_entity.replace('_','').replace('-','')
        if not glue_db_name:
            glue_db_name=client_database_name + '_' + upd_client_entity + '_' + 'raw'
        else:
            glue_db_name=glue_db_name + '_' + upd_client_entity + '_' + 'raw'
        return (client_account_id, client_entity, replicate, db_name, db_schema, glue_db_name)
    except Exception as e:
        raise Exception(f'Unable to get config details!  {e}')


# ---------------------------------------------------------------------
# Check if the given key is a file
# ---------------------------------------------------------------------      
def is_file(source_bucket, key, prefix):
    try:
        if (len(prefix) > 2):
            s3_client.head_object(Bucket= source_bucket, Key=key)
            return True
    except Exception as e:
        logger.info(f'key {key} in bucket {source_bucket} is not a valid file!')
        return False


# ---------------------------------------------------------------------
# Get details from the event
# ---------------------------------------------------------------------
def get_object_details(source_bucket, source_key):
    try:
        domain_name = source_key.split('/')[0:2][1]  # get the second prefix and assign it as the domain name
        object_name = source_key.split('/')[-1] # get the file name
        short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
        prefix=source_key.split('/')      
        
        is_ignore_object =  (False if short_path.find('-daas-gen-raw') == -1 else True)
        is_dot_folder_object = (False if short_path.rfind('.',0) == -1 else True)
        is_preprocessor = False
        extension = 'none'
        if is_ignore_object:
            process_type = 'none'
        elif is_dot_folder_object:
            if (False if object_name.find('access-config.txt') == -1 else True):
                process_type = 'access-control'
            elif (False if object_name.find('cleanup.txt') == -1 else True):
                process_type = 'metadata-purger'
            else:                                   # could be a folder or subfolders can be ignored
                is_ignore_object = True
                process_type = 'none'
        elif is_file(source_bucket, source_key, prefix) and object_name:
            extension = object_name.split('.')[-1].lower() # get the file extension.
            if extension == 'xml' or extension == 'xls' or extension == 'xlsx' or extension == 'md':
                is_preprocessor = True
                process_type = 'convert'
            else:
                process_type = 'metadata-generate'
        else:                                      # could be a folder or subfolder (patition keys)
            is_ignore_object = True
            process_type = 'none'
        return (domain_name, object_name, short_path, is_ignore_object, is_dot_folder_object, is_preprocessor, process_type, extension)
    except Exception as e:
        raise Exception(e)

# ---------------------------------------------------------------------
# Package the parameters to send it to step function as input
# ---------------------------------------------------------------------
def package_parameters(source_bucket, source_key, region, domain_name, commands):
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
        event_vars={}
        event_vars['account_id'] = client_account_id
        event_vars['entity'] = client_entity
        event_vars['glue_db_name'] = glue_db_name
        event_vars['glue_admin_role_name'] = glue_admin_role_name
        event_vars['gluejb_lambda_arn'] = target_gluejb_lambda_arn
        event_vars['src_bucket_name'] = source_bucket
        event_vars['src_source_name'] = source_name    
        event_vars['source_file_path'] = path
        event_vars['domain_name'] = domain_name
        event_vars['crawler_name'] = crawler_name
        event_vars['table_name'] = table_name
        event_vars['partitions'] = partitions
        event_vars['partition_values'] = partition_values
        event_vars['replicate'] = replicate
        event_vars['db_name'] = db_name
        event_vars['db_schema'] = db_schema
        event_vars['commands']=commands
        return (client_account_id, glue_db_name, region, event_vars)
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
                (domain_name, object_name, short_path, is_ignore_object, is_dot_folder_object, is_preprocessor, process_type, extension) = get_object_details(source_bucket, source_key)
                    
                if is_ignore_object:
                    resp= source_bucket +  '/' + source_key + ' is not a valid file.. processing ignored!'
                    logger.info(f'ignoring the object {source_key} since it is not a valid file to generate metadata...')
                elif is_preprocessor:
                    resp = invoke_converter_stepfunction(source_bucket, source_key, domain_name, object_name, extension, state_machine_arn=event_converter_stepfn_arn)
                    logger.info(f'preprocessor invoked! {source_key} is being converted...')
                else:
                    if is_dot_folder_object:                    
                        fileObj = s3_client.get_object(Bucket= source_bucket, Key=source_key)
                        commands = fileObj['Body'].read().decode('utf-8').splitlines()
                        logger.info(f'since the object is a configration {source_key}, commands are being packaged for processing....')
                    else:
                        commands='none'
                        logger.info(f'{source_key} is valid, routing to step funciton to generate metadata ...')
                    (client_account_id, glue_db_name, region, event_vars) = package_parameters(source_bucket, source_key, region, domain_name, commands)
                    params=json.dumps(event_vars)
                    resp = invoke_controller_stepfunction(client_account_id, glue_db_name, region, params, controller=process_type, state_machine_arn=event_controller_stepfn_arn)
                    logger.info(f'controller step function invoked!')
            return {
                'body': resp,
                'statusCode': 200
            }
        except Exception as e:
            return {
                'body': json.loads(json.dumps(e, default=str)),
                'statusCode': 400
            }
