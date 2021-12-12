#!/bin/bash
# set variables
entity=$1
accountId=$2
application=$3
environment=$4
region=$5
serviceType=$6
lambdaName=$7
lambdaVersion=$8
stackName=stk-$serviceType-$application
commonS3Folder=$entity-s3-$accountId-$region-common-artifacts-$environment
type=update

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then

    # Lambda service needs special handling...
    if [ serviceType == "lmd" ]
        # Default lambda version if none provided
        if [%8]==[]
              lambdaVersion=100
        
        # reset variables for lambda
        stackName=stk-$serviceType-$lambdaName
        functionName=$serviceType-$application

        # Compress lamdba source file
        powershell.exe Compress-Archive -LiteralPath ./$application/$functionName.py  -DestinationPath ./$application/$functionName-$lambdaVersion.zip

        # Copy zip file to common stack folder
        call aws s3 cp ./$application/$functionName-$lambdaVersion.zip ^
            s3://$commonS3Folder/$objectType/scripts/stacks/$stackName/$functionName-$version.zip

        # Copy the env var file to the common stack folder only when it exists
        file = ./$application/$stackName-env-var.yml
        if [[ -f "$file" ]];
        then
            call aws s3 cp %file  ^
                s3://$commonS3Folder/$objectType/scripts/stacks/$stackName/$stackName-env-var.yml
        fi
    fi

    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $stackName.yml \
       s3://$commonS3Folder/$objectType/scripts/stacks/$stackName/$stackName.yml

    # Check if stack already exists
    stackStatus=$(aws cloudformation describe-stacks --stack-name "${stackName}-${environment}" 2>&1)
    if echo "${stackStatus}" | grep 'not found';
        type=create

    # create the cloudformation stack
    aws cloudformation $type-stack \
        --stack-name $stackName-$environment \
        --region $region \
        --template-url https://s3-$region.amazonaws.com/$commonS3Folder/$serviceType/scripts/stacks/$stackName/$stackName.yml \
    	  --parameters ParameterKey=Environment,ParameterValue=$environment
else
  echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <application> <environment> <region> <service type> <<lambda name>> <<lambda version>"
fi
