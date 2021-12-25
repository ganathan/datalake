import copy
import json
import os
import urllib.parse
import boto3
import xmltodict
import openpyxl
import pandas as pd
from io import StringIO


# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    global s3_client
    s3_client = boto3.client('s3')

 
# -------------------------------------------------
# Convert excel file to csv
# -------------------------------------------------
def convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name):
    excel_file = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    df_sheet  = pd.read_excel(excel_file['Body'].read(), index_col=0, engine='openpyxl')
    csv_key = source_key.split('.')[0] + '.csv'
    csv_buffer = StringIO()
    df_sheet.to_csv(csv_buffer, sep="|")
    s3_client.put_object(Body=csv_buffer.getvalue(), Bucket=source_bucket, Key=csv_key)
    
    # move the original xml file to raw folder
    domain_end_index = short_path.find(domain_name) + len(domain_name)
    new_source_key = short_path[0:domain_end_index] + '-daas-gen-raw' + short_path[domain_end_index:len(short_path)] + '/' + object_name
    copy_source = { 'Bucket': source_bucket, 'Key': source_key }
    result = s3.meta.client.copy(copy_source,source_bucket,new_source_key)
    s3_client.delete_object(
        Bucket=source_bucket, 
        Key=source_key
    )

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    init()
    print(event)
    partition_values=[]
    source_bucket = event['bucket_name']
    source_key = urllib.parse.unquote_plus(event['file_key'], encoding='utf-8')
    object_name = source_key.split('/')[-1] # get the file name
    domain_name = source_key.split('/')[0:2][1]  # get the second prefix and assign it as the domain name
    short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
    is_dot_folder_object = short_path.rfind('.',0)
    is_ignore_object = short_path.find('-daas-gen-raw')
    if object_name and is_dot_folder_object == -1 and is_ignore_object == -1:
        source_name = source_key.split('/')[0:1][0]  # get the first prefix and assign it as the source name
        partitions = source_key.split('/')[2:-1]  # Remove source name, domain name in the front and the key at the end
        for key in partitions:
            value = key.split('=')[1]
            print(value)
            if value:
                partition_values.append(value)
            else:
                partition_values.append(key)
        extention = object_name.split('.')[-1] # get the file extension.
        path = 's3://' + source_bucket + '/' + source_name + '/' +  domain_name + '/'
        if extention.lower() == 'xls' or extention.lower() == 'xlsx':
            convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name)
        else:
            print('File is not XLS/EXCEL, so ignoring')