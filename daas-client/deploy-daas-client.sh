#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ] 
then
    # Deploy the VPC
    sh ../deploy-stack.sh $entity $accountId daas-client $environment $region vpc
    sleep 90
    # Deploy the Nat Gateway
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region ngw
    sh ../deploy-stack.sh $entity $accountId daas-client $environment $region ngw
    sleep 60
    # Deploy the buckets
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    sh ../deploy-stack.sh $entity $accountId daas-client-athena-log $environment $region s3
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    sh ../deploy-stack.sh $entity $accountId daas-client-raw-bucket $environment $region s3
    # Deploy the lambda
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmd
    sh ../deploy-stack.sh $entity $accountId metadata-generator $environment $region lmd 1
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi