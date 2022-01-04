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
    lambda_version=$3

    if [ "$app" == "" ]
    then
        $app="daas-core"
    fi

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $service_type

    if [ "$serviceType" != "tag" ]
    then
        # call the child stack
        sh ../deploy-stack.sh $entity $accountId $region $environment $service_type $app $lambda_version
    fi
}


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack tag
    # deploy_stack vpc
    # sleep 90
    # deploy_stack ngw
    # deploy_stack sqs ingest-daas-core 
    # deploy_stack sgrp lmd-default
    # deploy_stack lmdlyr xmltodict
    deploy_stack lmd ingest-invoker 1
    # deploy_stack lmd excel-processor 1
    # deploy_stack lmd xml-processor 1
    # deploy_stack stpfn event-converter

else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi

