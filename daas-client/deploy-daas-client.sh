#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4
daasCoreAccountId=$5


deploy_stack(){
    # process the arguments
    serviceType=$1
    app=$2
    lambdaVersion=$3

    if [ -z "$app" ]
    then
        app="daas-client"
    fi

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $serviceType

    if [ "$serviceType" != "tag" ]
    then
        # call the child stack
        sh ../deploy-stack.sh $entity $accountId $region $environment $serviceType $app $lambdaVersion $daasCoreAccountId
    fi
}

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack tag
    # deploy_stack vpc
    # sleep 90
    # deploy_stack ngw
    # deploy_stack s3 daas-client-athena-log
    # deploy_stack sgrp ec2-default
    # deploy_stack sgrp rds-pgrs-default
    # deploy_stack sgrp lmd-default
    # deploy_stack lmd metadata-generator 1

    # Create aurora serverless database manually, take note of username and password

    # Once the secrets manager is created update the username, password etc with its proper value in the console.
    # {"username": "xxxx", "password": "xxx", "endpoint": "xxxxxxx", "url":"jdbc:postgresql://xxxxx.xxxx.xxxxx.rds.amazonaws.com:5432/daas","port":"5432"}
    # deploy_stack smgr daas-client-pgsrvls 
    
    # deploy_stack glucon daas-client-pgsrvls
    # deploy_stack lmd glujb-sync-generator 1
    # rawQueueArn=arn:aws:sqs:$region:$daasCoreAccountId:$entity-sqs-curate-daas-core-$environment
    # deploy_stack s3 daas-client-test-raw-bucket rawQueueArn
    curateQueueArn=arn:aws:sqs:$region:$daasCoreAccountId:$entity-sqs-curate-daas-core-$environment
    deploy_stack s3 daas-client-test-cur-bucket $curateQueueArn $daasCoreAccountId
    # deploy_stack s3 daas-client-test-dist-bucket arn:aws:sqs:$region:$daasCoreAccountId:$entity-sqs-dist-daas-core-$environment
    # deploy_stack ec2 daas-client-bastn-host 

else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment> <<daas core account id>>"
fi