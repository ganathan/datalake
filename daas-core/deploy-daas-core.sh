#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4


deploy_stack(){
    # process the arguments
    service_type=$1
    app=$2
    lambda_version=$2

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region $service_type

    # call the child stack
    sh ../deploy-stack.sh $entity $accountId $app $environment $region $service_type $lambda_version
}


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ]  && [ ! -z "$environment" ] && [ ! -z "$region" ]
then
    # Deploy the tag
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region tag
    # Deploy the VPC
    # deploy_stack vpc daas-core
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region vpc
    # sh ../deploy-stack.sh $entity $accountId daas-core $environment $region vpc
    # sleep 90
    # Deploy the Nat Gateway
    # deploy_stack ngw daas-core
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region ngw
    # sh ../deploy-stack.sh $entity $accountId daas-core $environment $region ngw
    # sleep 60
    # Deploy the SQS Queue
    # deploy_stack sqs ingest-daas-core
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region sqs
    # sh ../deploy-stack.sh $entity $accountId ingest-daas-core $environment $region sqs
    # Deploy the Lambda Layer
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmdlyr
    # sh ../deploy-stack.sh $entity $accountId xmltodict $environment $region lmdlyr
    # Deploy the Security Group
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region sgrp
    # sh ../deploy-stack.sh $entity $accountId lmd-default $environment $region sgrp
    # Deploy the Lambda    
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmd
    # sh ../deploy-stack.sh $entity $accountId ingest-invoker $environment $region lmd 1
    # Deploy the step function
    deploy_stack stpfn event-converter
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi

