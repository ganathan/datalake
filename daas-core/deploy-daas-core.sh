#!/bin/bash
# set variables
entity=$1
accountId=$2

# Deploy the VPC
# sh ../deploy-stack.sh $entity $accountId daas-core dev us-west-2 vpc
# sleep 90
# sh ../deploy-stack.sh $entity $accountId daas-core dev us-west-2 ngw
# sleep 60
# sh ../deploy-stack.sh $entity $accountId ingest-daas-core dev us-west-2 sqs
sh ../deploy-stack.sh $entity $accountId xmltodict dev us-west-2 lmdlyr