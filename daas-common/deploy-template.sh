#!/bin/bash
# set variables
entity="$1"
accountId="$2"
environment="$3"
region="$4"
serviceType="$5"
templateName=cft-$serviceType-common
commonS3Bucket=$entity-s3-$accountId-$region-common-artifacts-$environment

# Check if common bucket exits
bucketstatus=$(aws s3api head-bucket --bucket "${commonS3Bucket}" 2>&1)
if echo "${bucketstatus}" | grep 'Not Found';
then
    #Create the common bucket first
    aws s3api  create-bucket --bucket $commonS3Bucket --region $region
    
    #Add tags to the common bucket
    aws s3api  put-bucket-tagging --bucket $bucketname --tagging 'TagSet=[{Key=Name,Value="'$commonS3Bucket'"}]'
fi

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $templateName-template.yml \
       s3://$commonS3Bucket/$serviceType/scripts/template/$templateName-template.yml
else
  echo "Missing required parameter. Usage: deploy-template.sh <entity> <account id> <environment> <region> <service type>"
fi

if [ serviceType == "lmd"]
then
    # Copy the environment variable to the common deploy folder
    aws s3 cp $templateName-env-var.yml \
       s3://$commonS3Folder/$objectType/scripts/template/$templateName-env-var.yml    
fi