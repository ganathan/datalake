#!/bin/bash
# set variables
layer=$1
entity=$2
accountId=$3
region=$4
environment=$5
serviceType=$6
app=$7
lambdaVersion=$8
secretString=$8
s3QueueArn=$8
ec2KeyPairName=$8
daasCoreAccountId=$9
daasCoreEntity=$10
stackName=stk-$serviceType-$app
commonS3Bucket=$entity-s3-$accountId-$region-common-artifacts-$environment
type=update

# Check if parameters are defined
if [ ! -z "$layer" ] && [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$region" ] && [ ! -z "$environment" ]  && [ ! -z "$serviceType" ] && [ ! -z "$app" ] 
then

    # Check if common bucket exists for the given service type
    if aws s3 ls "$commonS3Bucket" 2>&1 | grep -q 'bucket does not exist';
    then
      echo "common bucket not found! creating the common bucket"
      sh ../daas-common/deploy-template.sh $entity $accountId $region $environment $serviceType
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
        rm $layer/$serviceType-$app-$lambdaVersion.zip

        # Create a new zip file with the given version.
        zip -r -X $layer/$serviceType-$app-$lambdaVersion.zip $layer/$serviceType-$app.py
        sleep 5

        # Copy zip file to common stack folder
        aws s3 cp $layer/$serviceType-$app-$lambdaVersion.zip \
            s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$serviceType-$app-$lambdaVersion.zip

        # Copy the env var file to the common stack folder only when it exists
        file=$layer/$stackName-env-var.yml
        if [[ -f "$file" ]]; then
            aws s3 cp $file  \
                s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName-env-var.yml
        fi
    elif [ "$serviceType" == "lmdlyr" ]
    then
        # Copy layer zip file to common stack folder
        aws s3 cp $layer/$app.zip \
            s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$app.zip
    elif [ "$serviceType" == "rle" ]
    then
        # Copy the trust policy file to the common stack folder only when it exists
        file=$layer/$stackName-trust.yml
        if [[ -f "$file" ]]; then
            aws s3 cp $file  \
                s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName-trust.yml        
        fi
    elif [ "$serviceType" == "stpfn" ]
    then
        # Copy the var file to the common stack folder only when it exists
        file=$layer/$stackName-var.yml
        if [[ -f "$file" ]]; then
            aws s3 cp $file  \
                s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName-var.yml
        fi

        #Copy the statemachine json file to common stack folder 
        aws s3 cp $layer/$serviceType-$app.json \
            s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$serviceType-$app.json
    fi

    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $layer/$stackName.yml \
       s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml
       

    # Check if stack already exists
    # stackStatus=$(aws cloudformation describe-stacks --stack-name "${stackName}-${environment}" 2>&1)
    stackStatus=$(aws cloudformation describe-stacks --stack-name "${stackName}-${environment}" --region "${region}" 2>&1)
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
                        ParameterKey=LambdaZipFileName,ParameterValue=$stackName/$serviceType-$app-$lambdaVersion.zip \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM
    elif [ "$serviceType" == "s3" ]
    then
        if [ ! -z "$s3QueueArn" ]
        then
            # s3 bucket with event queue arn. 
            aws cloudformation $type-stack \
                --stack-name $stackName-$environment \
                --region $region \
                --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
                --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                        ParameterKey=EventQueueArn,ParameterValue=$s3QueueArn ParameterKey=DaasCoreAccountId,ParameterValue=$daasCoreAccountId \
                        ParameterKey=DaasCoreEntity,ParameterValue=$daasCoreEntity \
                --capabilities CAPABILITY_AUTO_EXPAND
        else
            # s3 bucket with no event queue arn.
            aws cloudformation $type-stack \
                --stack-name $stackName-$environment \
                --region $region \
                --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
                --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                --capabilities CAPABILITY_AUTO_EXPAND
        fi
    elif [ "$serviceType" == "ec2" ]
    then
        # check if key pair exists, else create one.
        echo $ec2KeyPairName
        keyPairStatus=$(aws ec2 wait key-pair-exists --region "${region}" --key-names "${ec2KeyPairName}" 2>&1)
        echo $keyPairStatus
        tst="{$keyPairStatus}.is there value"
        echo $tst
        if [ ! -z "$keyPairStatus" ]
        then
            aws ec2 create-key-pair --key-name $ec2KeyPairName --query "KeyMaterial" --region $region --output text > $ec2KeyPairName.pem
            
            # Copy the pem file to the common stack folder only when it exists
            file=$ec2KeyPairName.pem
            if [[ -f "$file" ]]; then
                aws s3 cp $file  \
                    s3://$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$ec2KeyPairName.pem
            fi

        fi

        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                        ParameterKey=KeyName,ParameterValue=$ec2KeyPairName ParameterKey=Region,ParameterValue=$region \
            --capabilities CAPABILITY_AUTO_EXPAND  
    elif [ "$serviceType" == "stpfn" ]
    then
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM
    elif [ "$serviceType" == "rle" ]
    then
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                         ParameterKey=DaasCoreAccountId,ParameterValue=$daasCoreAccountId ParameterKey=DaasCoreEntity,ParameterValue=$daasCoreEntity \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM
    elif [ "$serviceType" == "vpc" ]
    then
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
                        ParameterKey=Region,ParameterValue=$region \
            --capabilities CAPABILITY_AUTO_EXPAND  
    else
        # create or update the cloudformation stack
        aws cloudformation $type-stack \
            --stack-name $stackName-$environment \
            --region $region \
            --template-url https://s3-$region.amazonaws.com/$commonS3Bucket/$serviceType/scripts/stacks/$stackName/$stackName.yml \
            --parameters ParameterKey=Entity,ParameterValue=$entity ParameterKey=Environment,ParameterValue=$environment \
            --capabilities CAPABILITY_AUTO_EXPAND  
    fi
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <accountid> <region> <environment> <service type> <application> <<lambda version>>"
fi