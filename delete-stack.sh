#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4
serviceType=$5
app=$6
stackName=stk-$serviceType-$app
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment

if [ "$app" == "" ]
then
    $app="daas-client"
fi

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ]  && [ ! -z "$environment" ] && [ ! -z "$serviceType" ]
then
    # delete the cloudformation stack
    aws cloudformation delete-stack \
        --stack-name $stackName-$environment \
        --region $region
else
  echo "Missing required parameter. Usage: delete-stack.sh <entity> <accountid> <region> <environment> <service type> <application>"
fi
