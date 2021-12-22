#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ]  && [ ! -z "$environment" ] && [ ! -z "$region" ]
then
    # Deploy the VPC
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region vpc
    # sh ../deploy-stack.sh $entity $accountId daas-core $environment $region vpc
    # sleep 90
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region ngw
    # sh ../deploy-stack.sh $entity $accountId daas-core $environment $region ngw
    # sleep 60
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region sqs
    # sh ../deploy-stack.sh $entity $accountId ingest-daas-core $environment $region sqs
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmdlyr
    # sh ../deploy-stack.sh $entity $accountId xmltodict $environment $region lmdlyr
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmd
    sh ../deploy-stack.sh $entity $accountId ingest-invoker $environment $region lmd 1
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi