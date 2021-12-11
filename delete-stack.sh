#!/bin/bash
# set variables
application=$1
environment=$2
region=$3
serviceType=$4
stackName=stk-$serviceType-$application
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment


# Check if parameters are defined
if [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # delete the cloudformation stack
    aws cloudformation delete-stack \
        --stack-name $stackName-$environment \
        --region $region
else
  echo "Missing required parameter. Usage: delete-stack.sh <application> <environment> <region> <service type>"
fi
