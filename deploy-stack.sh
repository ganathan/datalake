#!/bin/bash
# set variables
entity=$1
accountId=$2
application=$3
environment=$4
region=$5
serviceType=$6
lambdaVersion=$7
secretString=$7
stackName=stk-$serviceType-$application
commonS3Bucket=$entity-s3-$accountId-$region-common-artifacts-$environment
type=update

echo $secretString

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$application" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ] 
then

    # Check if common bucket exists for the given service type
    if aws s3 ls "$commonS3Bucket" 2>&1 | grep -q 'bucket does not exist';
    then
      echo "common bucket not found! creating the common bucket"
      sh ../daas-common/deploy-template.sh $entity $accountId $environment $region $serviceType
    else
      echo "common bucket found!!"
    fi

    # Lambda service needs special handling...
    if [ "$serviceType" == "lmd" ]
    then
        # Default lambda version if none provided
        if [ -z "$lambdaVersion" ]
        then
            lambdaVersion=100
        fi

        # First delete the existing zip file. this ensures always a fresh zip file is created and deployed!
        rm $serviceType-$application-$lambdaVersion.zip

        # Create a new zip file with the given version.
        zip -r -X $serviceType-$application-$lambdaVersion.zip $serviceType-$application.py
        sleep 5

        # Copy zip file to common stack folder
        aws s3 cp $serviceType-$application-$lambdaVersion.zip \
            s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$serviceType-$application-$lambdaVersion.zip

        # Copy the env var file to the common stack folder only when it exists
        file=$stackName-env-var.yml
        if [[ -f "$file" ]]; then
            aws s3 cp $file  \
                s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName-env-var.yml
        fi
    elif [ "$serviceType" == "lmdlyr" ]
    then
        # Copy layer zip file to common stack folder
        aws s3 cp $application.zip \
            s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$application.zip
    fi

    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $stackName.yml \
       s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml

    # Check if stack already exists
    stackStatus=$(aws cloudformation describe-stacks --stack-name "${stackName}-${environment}" 2>&1)
    if echo "${stackStatus}" | grep 'does not exist'; then
        echo "switching to create stack"
        type=create
    fi

    if [ "$serviceType" == "lmd" ]
    then
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                        ParameterKey=LambdaZipFileName,ParameterValue=$stackName/$serviceType-$application-$lambdaVersion.zip \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM
    else
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment    
    fi
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <application> <environment> <region> <service type> <<lambda version>"
fi