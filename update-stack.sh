#!/bin/bash
# set variables
entity=$1
accountId=$2
application=$3
environment=$4
region=$5
serviceType=$6
lambdaVersion=$7
stackName=stk-$serviceType-$application
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment


# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Deploy the stack first
    sh deploy-$serviceType.sh $entity $accountId $application $environment $region $serviceType $lambdaVersion

    # create the cloudformation stack
    aws cloudformation update-stack \
        --stack-name $stackName-$environment \
        --region $region \
        --template-url https://s3-$region.amazonaws.com/$commonS3Folder/$serviceType/scripts/stacks/$stackName/$stackName.yml \
    	  --parameters ParameterKey=Environment,ParameterValue=$environment
else
  echo "Missing required parameter. Usage: update-stack.sh <entity> <account id> <application> <environment> <region> <service type>"
fi
