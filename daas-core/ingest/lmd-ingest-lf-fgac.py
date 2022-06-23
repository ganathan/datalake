import json
import boto3
import os

# ---------------------------------------------------------------------------
# get the root command from the command string
# ---------------------------------------------------------------------------
def get_root_command(command):
    if command == 'GRANT':
        root_command='grant'
    elif command == 'REVOKE':
        root_command='revoke'
    elif command == 'LIST':
        root_command='list'
    else:
        root_command='unknown'
    return root_command

# ---------------------------------------------------------------------------
# get columns or rows to be filtered from the command string
# ---------------------------------------------------------------------------
def get_columns(filter, command_components):
    cols=[]
    row_filters=""
    index=4
    command_type=""
    if filter=='COLUMNS':
        command_type='grant_with_col'
        for index in range(5,len(command_components)):
            if command_components[index] == 'TO':
                break
            else:
                col = command_components[index].strip()
                col_len = len(col)
                if col[-1] == ',':
                    col = col[0:(col_len-1)]
                cols.append(col)
    elif filter=='ROWS':
        command_type='grant_with_row'
        for index in range(5,len(command_components)):
            if command_components[index] == 'TO':
                break
            else:
                row_filters += command_components[index] + ' '
    return (cols, row_filters, command_type, index)

# ---------------------------------------------------------------------------
# get filter from the command string
# ---------------------------------------------------------------------------
def get_filter(command_components):
    try:
        filter=command_components[4]
    except IndexError:
        filter='null'
    return filter

# ---------------------------------------------------------------------------
# get role arn from the command string
# ---------------------------------------------------------------------------
def get_role_arn(account_id, index, command_components):
    try:
        role_arn='arn:aws:iam::' + account_id + ':user/' + command_components[index+1]
        print(role_arn)
    except IndexError:
        role_arn='null'
    return role_arn

# ---------------------------------------------------------------------------
# parse the command string read from the config file for a given daas client
# ---------------------------------------------------------------------------
def parse(command, account_id):
    command_components = command.split()
    root_command = get_root_command(command_components[0].upper())
    permission=[command_components[1]]
    table_name=command_components[3]
    filter=get_filter(command_components)
    (cols, row_filters, command_type, index) = get_columns(filter, command_components)
    role_arn = get_role_arn(account_id, index, command_components)
    return (root_command, command_type, permission, table_name, cols, row_filters.strip(), role_arn)


# -------------------------------------------------
# get the glue daas client
# -------------------------------------------------
def get_lakeformation_client(region, target_lf_service_role_arn):
    try:
        url='https://sts.' + region + '.amazonaws.com/'
        sts_connection = boto3.client('sts', region_name=region, endpoint_url=url)
        
        daas_client = sts_connection.assume_role(
            RoleArn=target_lf_service_role_arn,
            RoleSessionName="daas-core"
        )
        ACCESS_KEY = daas_client['Credentials']['AccessKeyId']
        SECRET_KEY = daas_client['Credentials']['SecretAccessKey']
        SESSION_TOKEN = daas_client['Credentials']['SessionToken']
        lf_client = boto3.client('glue', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)
        return lf_client
    except Exception as e:
        raise Exception(f'Unable to assume role {target_lf_service_role_arn}! {e}')

# ------------------------------------------------------------
# get the resource mapped either with rows or columns or none
# ------------------------------------------------------------
def get_resource(command_type,database_name,table_name,cols,row_filters):
    if command_type=='grant_with_col':
        resource = { 'TableWithColumns': { 'DatabaseName': database_name, 'Name': table_name, 'ColumnNames': cols } }
    elif command_type=='grant_with_row':
        resource = { 'DataCellsFilter': { 'DatabaseName': database_name, 'TableName': table_name, 'Name': row_filters } }
    else:
        resource = { 'Table' : { 'DatabaseName': database_name, 'Name': table_name} }
    return resource

# ------------------------------------------------------------
# revoke iam principals on the given table in daas client
# ------------------------------------------------------------
def revoke_iam_principals(lf_client, account_id, database_name, table_name):
    principal_role='IAM_ALLOWED_PRINCIPALS'
    command_string='REVOKE ALL ON ' + table_name + ' TO IAM_ALLOWED_PRINCIPALS'
    principal = { 'DataLakePrincipalIdentifier' : principal_role}
    resource = { 'Table' : { 'DatabaseName': database_name, 'Name': table_name} }
    permissions = ['ALL']
    try:
        resp = lf_client.revoke_permissions(CatalogId=account_id,Principal=principal,Resource=resource,Permissions=permissions)
    except Exception as e:
        print('IAM_ALLOWED_PRINCIPALS does not exist .. ignoring!')


# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    try:
        print(event)
        database_name = event['database_name']
        account_id = event['account_id']
        region = event['region']
        params = event['params']
        responses = []
        for command in params:
            target_lf_service_role_arn='arn:aws:iam::' + account_id + ':role/' + os.environ["ENV_VAR_LF_SERVICE_ROLE"]
            lf_client = get_lakeformation_client(region, target_lf_service_role_arn)
            (root_command, command_type, permission, table_name, cols, row_filters, role_arn) = parse(command, account_id)
            revoke_iam_principals(lf_client, account_id, database_name, table_name)
            principal = { 'DataLakePrincipalIdentifier' : role_arn }
            permissions = permission
            resource = get_resource(command_type,database_name,table_name,cols,row_filters)

            if root_command=='revoke':
                resp = lf_client.revoke_permissions(CatalogId=account_id,Principal=principal,Resource=resource,Permissions=permissions)
            elif root_command=='grant':
                resp = lf_client.grant_permissions(CatalogId=account_id,Principal=principal,Resource=resource,Permissions=permissions)
            elif root_command=='list' and role_arn!='null':
                resp = lf_client.list_permissions(CatalogId=account_id,Principal=principal,Resource=resource)
            else:
                resp = lf_client.list_permissions(CatalogId=account_id,Resource=resource)
            responses.append(json.dumps({ "command": command}))
            responses.append(resp)
        return {
            'body': responses,
            'statusCode': 200
        }
    except Exception as e:
        return {
            'body': json.loads(json.dumps(e, default=str)),
            'statusCode': 400
        }
