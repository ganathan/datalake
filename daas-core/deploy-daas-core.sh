#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4


deploy_stack(){
    # process the arguments
    layer=$1
    serviceType=$2
    app=$3
    lambdaVersion=$4

    if [ -z "$app" ]
    then
        app="daas-core"
    fi

    echo 'b4 calling deply tmplt'
    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $serviceType

    echo 'aftr calling deply tmplt'
    if [ "$serviceType" != "tag" ]
    then
        # call the child stack
        sh ../deploy-stack.sh $layer $entity $accountId $region $environment $serviceType $app $lambdaVersion
    fi
}


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack setup tag
    
    # NOTE: Setup Layer.. optional if you prefer to use existing vpc and ngw
    # deploy_stack setup vpc
    # sleep 90
    # deploy_stack setup ngw
    # sleep 30


    # deploy_stack setup sgrp lmd-default
    # deploy_stack setup lmdlyr xmltodict
    # deploy_stack setup lmdlyr cryptography
    # deploy_stack setup s3 daas-core-setup-bucket    
    # sleep 90

    # NOTE: open the id-config.csv file and update the account id with the appropriate client account id.
    # bucketPath=$entity-s3-$region-daas-core-setup-bucket-$environment
    # aws s3 cp ./setup/setup.csv s3://$bucketPath/.daas-setup/setup.csv
    # aws s3 cp ./setup/id-config.csv s3://$bucketPath/.daas-setup/id-config.csv
    # sleep 90

    # NOTE: Ingestion Layer
    # deploy_stack ingest sqs ingest-daas-core 
    # sleep 90
    deploy_stack ingest lmd ingest-invoker 1
    # deploy_stack ingest lmd ingest-metadata-generator 1
    # deploy_stack ingest lmd ingest-metadata-purger 1  
    # deploy_stack ingest lmd excel-processor 1
    # deploy_stack ingest lmd xml-processor 1
    # deploy_stack ingest stpfn ingest-event-controller
    # deploy_stack ingest stpfn event-converter
    # sleep 90
    
    # For lakeformation FGAC ---->
    # deploy_stack ingest lmd ingest-lf-fgac 1

    # NOTE: Curation Layer ----->
    # deploy_stack curate sqs curate-daas-core 
    # deploy_stack curate lmd curate-model-generator 1
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi

