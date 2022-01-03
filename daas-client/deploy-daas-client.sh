#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4


deploy_stack(){
    # process the arguments
    service_type=$1
    app=$2
    lambda_version=$3

    if [ "$app" == "" ]
    then
        $app="daas-client"
    fi

    # call the common template
    sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $service_type

    if [ "$serviceType" != "tag" ]
    then
        # call the child stack
        sh ../deploy-stack.sh $entity $accountId $region $environment $service_type $app $lambda_version
    fi
}

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ] 
then

    # deploy_stack tag
    # deploy_stack vpc
    # sleep 90
    # deploy_stack ngw
    # deploy_stack s3 daas-client-athena-log
    # deploy_stack s3 daas-client-test-raw-bucket
    # deploy_stack s3 daas-client-test-cur-bucket
    # deploy_stack s3 daas-client-test-dist-bucket
    # deploy_stack sgrp ec2-default
    # deploy_stack sgrp rds-pgrs-default
    # deploy_stack sgrp lmd-default
    # deploy_stack smgr daas-client-pgsrvls 
    # deploy_stack glucon daas-client-pgsrvls 
    # deploy_stack lmd metadata-generator 1
    # deploy_stack lmd glujb-sync-generator 1

    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region vpc
    # sh ../deploy-stack.sh $entity $accountId daas-client $environment $region vpc
    # sleep 90
    # Deploy the Nat Gateway
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region ngw
    # sh ../deploy-stack.sh $entity $accountId daas-client $environment $region ngw
    #sleep 60
    # Deploy the buckets
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    # sh ../deploy-stack.sh $entity $accountId daas-client-athena-log $environment $region s3
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    # sh ../deploy-stack.sh $entity $accountId daas-client-test-raw-bucket $environment $region s3
    # sh ../deploy-stack.sh $entity $accountId daas-client-test-cur-bucket $environment $region s3
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region sgrp
    # Deploy common security groups
    # sh ../deploy-stack.sh $entity $accountId lmd-default $environment $region sgrp
    sh ../deploy-stack.sh $entity $accountId ec2-default $environment $region sgrp  
    sh ../deploy-stack.sh $entity $accountId rds-pgrs-default $environment $region sgrp    
    # Deploy the metadata generator lambda
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmd
    # sh ../deploy-stack.sh $entity $accountId metadata-generator $environment $region lmd 1
    # Deploy the secrets manager for postgres srvlss
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region smgr
    # sh ../deploy-stack.sh $entity $accountId daas-client-pgsrvls $environment $region smgr
    # Deploy the Glue connection
    #sh ../daas-common/deploy-template.sh $entity $accountId $environment $region glucon
    #sh ../deploy-stack.sh $entity $accountId daas-client-pgsrvls $environment $region glucon
    # Deploy the glue job generator lambda
    # sh ../deploy-stack.sh $entity $accountId glujb-sync-generator $environment $region lmd 1   
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi