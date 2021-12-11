#!/bin/bash
# set variables
entity="$1"
environment="$2"
region="$3"
serviceType="$4"
stackName=cft-$serviceType-common-template
commonS3Folder=$entity-s3-$region-common-artifacts-$environment

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $stackName.yml \
       s3://$commonS3Folder/$serviceType/scripts/template/$stackName.yml
else
  echo "Missing required parameter. Usage: deploy-template.sh <entity> <environment> <region> <service type>"
fi
