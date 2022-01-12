import json
import boto3
import os
from io import StringIO

def init():
    global s3, s3_client, glue_client, trg_connection_name, trg_glue_srvc_role, entity, environment
    s3 = boto3.resource('s3')
    s3_client=boto3.client('s3')
    glue_client=boto3.client('glue')
    trg_connection_name=glue_db_name = os.environ["ENV_VAR_GLUE_CONNECTION"]
    trg_glue_srvc_role = os.environ["ENV_VAR_GLUE_SERVICE_ROLE"]
    entity = os.environ["ENV_VAR_ENTITY"]
    environment = os.environ['ENV_VAR_ENVIRONMENT']

def get_source_table(src_database_name, src_table_name):
    src_table = glue_client.get_table(DatabaseName=src_database_name, Name=src_table_name)['Table']
    return src_table
    
def get_source_columns(src_table):
    src_columns = src_table['StorageDescriptor']['Columns']
    return src_columns

def get_source_partitions(src_table):
    src_partitions = src_table['PartitionKeys']
    return src_partitions

def get_header_info():
    header_info= (
        'import sys\n'
        'from awsglue.transforms import *\n'
        'from awsglue.utils import getResolvedOptions\n'
        'from pyspark.context import SparkContext\n'
        'from awsglue.context import GlueContext\n'
        'from awsglue.job import Job\n'
        '\n'
        '## @params: [JOB_NAME]\n'
        'args = getResolvedOptions(sys.argv, [\'JOB_NAME\'])\n'
        '\n'
        'sc = SparkContext()\n'
        'glueContext = GlueContext(sc)\n'
        'spark = glueContext.spark_session\n'
        'job = Job(glueContext)\n'
        'job.init(args[\'JOB_NAME\'], args)\n')
    return header_info

def get_read_catalog(src_database_name, src_table_name):
    read_catalog= (
        '## @type: DataSource\n'
        '## @args: [database = "'+ src_database_name + '", table_name = "'+ src_table_name +'", transformation_ctx = "datasource0"]\n'
        '## @return: datasource0\n'
        '## @inputs: []\n'
        'datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "'+ src_database_name + '", table_name = "'+ src_table_name +'", transformation_ctx = "datasource0")\n')
    return read_catalog

def get_apply_map(src_columns, src_partitions):
    src_column_string = get_column_string(src_columns, src_partitions)
    apply_map= (
        '## @type: ApplyMapping\n'
        '## @args: [mapping = '+ src_column_string +', transformation_ctx = "applymapping1"]\n'
        '## @return: applymapping1\n'
        '## @inputs: [frame = datasource0]\n'
        'applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = '+ src_column_string +', transformation_ctx = "applymapping1")\n')
    return apply_map

def get_resolve_choice():
    resolve_choice= (
        '## @type: ResolveChoice\n'
        '## @args: [choice = "make_cols", transformation_ctx = "resolvechoice2"]\n'
        '## @return: resolvechoice2\n'
        '## @inputs: [frame = applymapping1]\n'
        'resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_cols", transformation_ctx = "resolvechoice2")\n')
    return resolve_choice

def get_drop_null():
    drop_null= (
        '## @type: DropNullFields\n'
        '## @args: [transformation_ctx = "dropnullfields3"]\n'
        '## @return: dropnullfields3\n'
        '## @inputs: [frame = resolvechoice2]\n'
        'dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")\n')
    return drop_null


def get_write_frame(trg_table_name, trg_database_name, trg_database_schema_name):
    trg_table = trg_database_schema_name + '.' + trg_table_name
    write_frame= ( 
        '## @type: DataSink\n'
        '## @args: [catalog_connection = "'+ trg_connection_name +'", connection_options = {"dbtable": "'+ trg_table +'", "database": "'+ trg_database_name +'"}, transformation_ctx = "datasink4"]\n'
        '## @return: datasink4\n'
        '## @inputs: [frame = dropnullfields3]\n'
        'datasink4 = glueContext.write_dynamic_frame.from_jdbc_conf(frame = dropnullfields3, catalog_connection = "'+ trg_connection_name +'", connection_options = {"dbtable": "'+ trg_table +'", "database": "'+ trg_database_name +'"}, transformation_ctx = "datasink4")\n'
        'job.commit()')
    return write_frame

def get_column_string(src_columns, src_partitions):
    col_str='['
    for column in src_columns:
        col_name=json.dumps(column['Name']) 
        col_type=json.dumps(column['Type'])
        if col_type=='\"bigint\"': col_type='\"long\"'
        col_str = col_str +  '(' + col_name + ', ' + col_type + ', ' + col_name + ', ' + col_type + '), '

    for partition in src_partitions:
        part_name=json.dumps(partition['Name'])
        part_type=json.dumps(partition['Type'])
        col_str = col_str + '(' + part_name + ', ' + part_type + ', ' + part_name + ', ' + part_type + '), '
    
    col_str = col_str[:-2] + ']'
    return col_str
    
def create_glue_job(glue_job_name, script_location, script_temp_location):
    job = glue_client.create_job(
        Name=glue_job_name, 
        Role=trg_glue_srvc_role,
        Connections={'Connections':[trg_connection_name]},
        Command={'Name':'glueetl', 'ScriptLocation': script_location},
        GlueVersion='3.0',
        Tags={'AppCategory':'daas'},
        DefaultArguments={
            '--job-bookmark-option': 'job-bookmark-enable',
            '--TempDir': script_temp_location
        })
    print(job)
    resp = glue_client.start_job_run(JobName=job['Name'])
    print(resp)


def lambda_handler(event, context):
    try:
        init()
        print(event)
        src_bucket_name= json.dumps(event['src_bucket_name']).strip('"')
        src_source_name=json.dumps(event['src_source_name']).strip('"')
        src_table_name=json.dumps(event['src_dataset_name']).strip('"')
        src_database_name=json.dumps(event['src_database_name']).strip('"')  
        trg_table_name=json.dumps(event['trg_table_name']).strip('"')
        trg_database_name=json.dumps(event['trg_database_name']).strip('"')
        trg_database_schema_name=json.dumps(event['trg_database_schema_name']).strip('"')
        glue_job_name = entity + '_glujb_' + src_table_name + '_' + environment
        glue_job_dir = src_source_name + '/.daas-config/glue-jobs'
        glue_job_key= glue_job_dir + '/scripts/' + glue_job_name + '.py'
        script_location = 's3://' + src_bucket_name + '/' + glue_job_key
        script_temp_location = 's3://' + src_bucket_name + '/' + glue_job_dir + '/temp/' 
        src_table = get_source_table(src_database_name, src_table_name)
        src_columns= get_source_columns(src_table)
        src_partitions = get_source_partitions(src_table)

        print('1')
        print('2')
        try:
            print('3')
            job = glue_client.get_job( JobName=glue_job_name )
            print(job)
            print('4')
        except Exception as e:
            print(e)
            print('5')
            script_buffer=StringIO()
            script_buffer.write(get_header_info())
            script_buffer.write(get_read_catalog(src_database_name, src_table_name))
            script_buffer.write(get_apply_map(src_columns, src_partitions))
            script_buffer.write(get_resolve_choice())
            script_buffer.write(get_drop_null())
            script_buffer.write(get_write_frame(trg_table_name, trg_database_name, trg_database_schema_name))
            s3_client.put_object(Body=script_buffer.getvalue(), Bucket=src_bucket_name, Key=glue_job_key)
            create_glue_job(glue_job_name, script_location, script_temp_location)
        print('6')
        glue_client.start_job_run( JobName=glue_job_name )
        return {
            'statusCode': 200,
            'body': json.dumps("done")
        }
    except Exception as e:
        print(e)
        return {
            'body': e,
            'statusCode': 400
        }
# f=open("gluepatinetjob.txt",'a',encoding='utf-8')
# f.write(header_info)
# f.write(read_catalog)
# f.write(apply_map)
# f.write(resolve_choice)
# f.write(drop_null)
# f.write(write_frame)
# f.close()