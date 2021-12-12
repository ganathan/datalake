#!/bin/bash
# set variables
entity=$1
accountId=$2
application=$3
environment=$4
region=$5
serviceType=$6
stackName=stk-$serviceType-$application
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $stackName.yml \
       s3://$commonS3Folder/$objectType/scripts/stacks/$stackName/$stackName.yml
else
  echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <application> <environment> <region> <service type>"
fi
