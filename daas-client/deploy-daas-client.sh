#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4
daasCoreAccountId=$5
ec2KeyPairName=$6
daasCoreEntity=$6

deploy_stack(){
    # process the arguments
    layer=$1
    serviceType=$2
    app=$3
    lambdaVersion=$4

    if [ -z "$app" ]
    then
        app="daas-client"
    fi

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $serviceType

    if [ "$serviceType" == "s3" ] || [ "$serviceType" == "rle" ]
    then
       
        # call the child stack
        sh ../deploy-stack.sh $layer $entity $accountId $region $environment $serviceType $app $lambdaVersion $daasCoreAccountId $daasCoreEntity
    elif [ "$serviceType" != "tag" ]
    then
      
        # call the child stack
        sh ../deploy-stack.sh $layer $entity $accountId $region $environment $serviceType $app $lambdaVersion $daasCoreAccountId
    fi


}

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack setup tag
    # deploy_stack setup vpc
    # sleep 90

    # deploy_stack setup ngw
    # deploy_stack setup s3 daas-client-athena-log
    # sleep 90

    # deploy_stack setup sgrp ec2-default
    # deploy_stack setup sgrp rds-pgrs-default
    # deploy_stack setup sgrp lmd-default
    # sleep 90

    # Create aurora serverless postgres database manually, take note of username and password
    # Provide the following: DB cluster identifer , Master username , Maseter Password, Min ACU, Max ACU and initial database name to create the db.
    # No public access.. 
    # Once the secrets manager is created update the username, password etc with its proper value in the console.
    # {"username": "xxxx", "password": "xxx", "endpoint": "<replace with end point>", "url":"jdbc:postgresql://<replace with resource ID>.rds.amazonaws.com:5432/daas","port":"5432"}
    # deploy_stack setup smgr pgrs-srvls-db 
    # sleep 90

    # deploy_stack setup glucon pgrs-srvls-db
    # deploy_stack setup lmd glujb-sync-generator 2
    
    # NOTE: to deploy the client s3 bucket and role use syntax:
    # sh deploy-daas-client.sh <entity> <client account id> <region> <environment> <core account id> <core entity>
    # deploy_stack ingest rle ingest-glue-controller-admin $daasCoreAccountId $daasCoreEntity
    # rawQueueArn=arn:aws:sqs:$region:$daasCoreAccountId:$daasCoreEntity-sqs-ingest-daas-core-$environment
    # deploy_stack ingest s3 lf-raw-sample-bucket $rawQueueArn $daasCoreAccountId $daasCoreEntity
    # sleep 90

    # create a keypair (pem file). Go to ec2 in cosole choose Create Key Pair and provide name <entity>-ec2-bastion-host.pem Add tag as needed. Browser will download the file.
    # deploy ec2 with additional parameters. <NOTE: daas core account id and pem key created above>
    # deploy_stack setup ec2 daas-client-bastn-host 
    # sleep 90

    # For lakeformation FGAC ---->
    # NOTE: to deploy the role use syntax:
    # sh deploy-daas-client.sh <entity> <client account id> <region> <environment> <core account id> <core entity>
    # deploy_stack ingest rle ingest-lf-fgac-admin $daasCoreAccountId $daasCoreEntity

    # For curation Layer --->
    # curateQueueArn=arn:aws:sqs:$region:$daasCoreAccountId:$entity-sqs-curate-daas-core-$environment
    # deploy_stack s3 daas-client-test-cur-bucket $curateQueueArn $daasCoreAccountId $daasCoreEntity    
    # deploy_stack s3 daas-client-test-dist-bucket arn:aws:sqs:$region:$daasCoreAccountId:$entity-sqs-dist-daas-core-$environment


else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment> <<daas core account id>> <<ec2 key pair name>>"
fi