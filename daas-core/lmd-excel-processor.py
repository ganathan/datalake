import copy
import json
import boto3
import xmltodict
import openpyxl
import pandas as pd
from io import StringIO


# -------------------------------------------------
# Convert excel file to csv
# -------------------------------------------------
def convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name):
    s3_client = boto3.client('s3')
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
    return result

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    try:
        source_bucket = event['source_bucket_name']
        source_key = event['source_key']
        domain_name = event['domain_name']
        object_name = event['object_name']
        short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
        result = convert_excel_to_csv(source_bucket, source_key, short_path, domain_name, object_name)
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
