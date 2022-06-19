#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4


deploy_stack(){
    # process the arguments
    serviceType=$1
    app=$2
    lambdaVersion=$3

    if [ -z "$app" ]
    then
        app="daas-core"
    fi

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $serviceType

    if [ "$serviceType" != "tag" ]
    then
        # call the child stack
        sh ../deploy-stack.sh $entity $accountId $region $environment $serviceType $app $lambdaVersion
    fi
}


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack tag
    # deploy_stack vpc
    # sleep 90
    
    # deploy_stack ngw
    # deploy_stack sgrp lmd-default
    # deploy_stack lmdlyr xmltodict
    # deploy_stack s3 daas-core-setup-bucket    
    # sleep 90

    # NOTE: open the id-config.csv file and update the account id with the appropriate client account id.
    # bucketPath=$entity-s3-$region-daas-core-setup-bucket-$environment
    # aws s3 cp ../setup.csv s3://$bucketPath/.daas-setup/setup.csv
    # aws s3 cp ../id-config.csv s3://$bucketPath/.daas-setup/id-config.csv
    # sleep 90

    # NOTE: Ingestion Layer
    # deploy_stack sqs ingest-daas-core 
    deploy_stack lmd ingest-invoker 1
    # deploy_stack lmd ingest-metadata-generator 1
    # deploy_stack lmd raw-metadata-purger 1  
    # deploy_stack lmd excel-processor 1
    # deploy_stack lmd xml-processor 1
    # deploy_stack stpfn ingest-event-controller
    # sleep 90

    # deploy_stack stpfn event-converter
    # sleep 90
    
    # NOTE: Curation Layer
    # deploy_stack sqs curate-daas-core 
    # deploy_stack lmd curate-model-generator 1
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi

