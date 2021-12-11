#!/bin/bash
# set variables
entity="$1"
accountId="$2"
environment="$3"
region="$4"
serviceType="$5"
stackName=cft-$serviceType-common
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $stackName-template.yml \
       s3://$commonS3Folder/$serviceType/scripts/template/$stackName-template.yml
else
  echo "Missing required parameter. Usage: deploy-template.sh <entity> <account id> <environment> <region> <service type>"
fi

if [ serviceType == "lmd"]
then
    # Copy the environment variable to the common deploy folder
    aws s3 cp $stackName-env-var.yml \
       s3://$commonS3Folder/$objectType/scripts/template/$stackName-env-var.yml
    
fi