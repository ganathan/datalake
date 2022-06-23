import copy
import json
import boto3
import xmltodict
import openpyxl
import pandas as pd
import logging
from io import StringIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -------------------------------------------------
# Convert excel file to csv
# -------------------------------------------------
def convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name):
    try:
        s3_client = boto3.client('s3')
        s3 = boto3.resource('s3')
        excel_file = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        logger.info(f'reading {source_key} file from {source_bucket}')
        df_sheet  = pd.read_excel(excel_file['Body'].read(), index_col=0, engine='openpyxl')
        csv_key = source_key.split('.')[0] + '.csv'
        logger.info(f'converting to excel file to {csv_key}')    
        csv_buffer = StringIO()
        df_sheet.to_csv(csv_buffer, sep="|")
        s3_client.put_object(Body=csv_buffer.getvalue(), Bucket=source_bucket, Key=csv_key)
        logger.info(f'persisting {csv_key} in {source_bucket}')
    
        # move the original xml file to raw folder
        domain_end_index = short_path.find(domain_name) + len(domain_name)
        new_source_key = short_path[0:domain_end_index] + '-daas-gen-raw' + short_path[domain_end_index:len(short_path)] + '/' + object_name
        copy_source = { 'Bucket': source_bucket, 'Key': source_key }
        result = s3.meta.client.copy(copy_source,source_bucket,new_source_key)
        s3_client.delete_object(
            Bucket=source_bucket, 
            Key=source_key
        )
        logger.info(f'moving the original {source_key} to {new_source_key}')    
        return f'{source_key} successfully converted...'
    except Exception as e:
        raise  Exception(f'Unable to convert {source_key}. Error {e}')

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    try:
        print(event)
        source_bucket = event['source_bucket']
        source_key = event['source_key']
        domain_name = event['domain_name']
        object_name = event['object_name']
        short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
        result = convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name)
        return {
            'body': result,
            'statusCode': 200
        }
    except Exception as e:
        print(e)
        return {
            'body': json.loads(json.dumps(e, default=str)),
            'statusCode': 400
        }
