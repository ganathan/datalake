import copy
import json
import os
import urllib.parse
import boto3
import hashlib
import xmltodict
import openpyxl
import pandas as pd
import logging
from io import StringIO


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -------------------------------------------------
# Convert xml file to json
# -------------------------------------------------
def convert_xml_to_json(source_bucket, source_key, short_path, domain_name, object_name):
    try:
        s3_client = boto3.client('s3')
        s3 = boto3.resource('s3')
        xml_file = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        data_dict = xmltodict.parse(xml_file['Body'].read())
        logger.info(f'reading {source_key} file from {source_bucket}')
        json_data = json.dumps(data_dict).replace('@','').replace('#text','text').replace('xmlns:','xmlns_').replace('xsi:','xsi_').replace('sdtc:','sdtc_')
        json_key = source_key.split('.')[0] + '.json'
        logger.info(f'converting to json file to {json_key}')
        s3_client.put_object(Body=json_data, Bucket=source_bucket, Key=json_key)
        logger.info(f'persisting {json_key} in {source_bucket}')
        
        # move the original xml file to raw folder
        domain_end_index = short_path.find(domain_name) + len(domain_name)
        new_source_key = short_path[0:domain_end_index] + '-daas-gen-raw' + short_path[domain_end_index:len(short_path)] + '/' + object_name
        copy_source = { 'Bucket': source_bucket, 'Key': source_key }
        result = s3.meta.client.copy(copy_source,source_bucket,new_source_key)
        s3_client.delete_object(Bucket=source_bucket, Key=source_key)
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
        result = convert_xml_to_json(source_bucket, source_key, short_path, domain_name, object_name)
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
