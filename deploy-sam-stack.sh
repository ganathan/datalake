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
daasCoreEntity=${10}
stackName=stk-$serviceType-$app
commonS3Bucket=$entity-s3-$accountId-$region-common-artifacts-$environment


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

    # Services that needs special handling...
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
       

    if [ "$serviceType" == "lmd" ]
    then
        # create or update the lambda using sam
        sam deploy -t $layer/$stackName.yml \
            --stack-name $stackName-$environment \
            --s3-bucket $commonS3Bucket \
            --s3-prefix $serviceType/scripts/stacks/$stackName \
            --parameter-overrides Entity=$entity Environment=$environment \
                    LambdaZipFileName=$stackName/$serviceType-$app-$lambdaVersion.zip \
            --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM  CAPABILITY_AUTO_EXPAND \
            --region $region \
            --no-fail-on-empty-changeset
        
    elif [ "$serviceType" == "s3" ]
    then
        echo "inside the s3 service type before sam deploy"
        if [ ! -z "$s3QueueArn" ]
        then
            # create or update s3 bucket using sam with daas queue arn notification.        
            sam deploy -t $layer/$stackName.yml \
                --stack-name $stackName-$environment \
                --s3-bucket $commonS3Bucket \
                --s3-prefix $serviceType/scripts/stacks/$stackName \
                --parameter-overrides Entity=$entity Environment=$environment \
                    EventQueueArn=$s3QueueArn DaasCoreAccountId=$daasCoreAccountId DaasCoreEntity=$daasCoreEntity \
                --capabilities CAPABILITY_AUTO_EXPAND \
                --region $region \
                --no-fail-on-empty-changeset
        else
            # create or update s3 bucket using sam with no event queue arn.        
            sam deploy -t $layer/$stackName.yml \
                --stack-name $stackName-$environment \
                --s3-bucket $commonS3Bucket \
                --s3-prefix $serviceType/scripts/stacks/$stackName \
                --parameter-overrides Entity=$entity Environment=$environment \
                --capabilities CAPABILITY_AUTO_EXPAND \
                --region $region \
                --no-fail-on-empty-changeset
        fi
    elif [ "$serviceType" == "ec2" ]
    then
        # check if key pair exists, else create one.
        keyPairStatus=$(aws ec2 wait key-pair-exists --region "${region}" --key-names "${ec2KeyPairName}" 2>&1)
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

        # create or update ec2 instance using sam
        sam deploy -t $layer/$stackName.yml \
            --stack-name $stackName-$environment \
            --s3-bucket $commonS3Bucket \
            --s3-prefix $serviceType/scripts/stacks/$stackName \
            --parameter-overrides Entity=$entity Environment=$environment \
                KeyName=$ec2KeyPairName Region=$region \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM \
            --region $region \
            --no-fail-on-empty-changeset
        
    elif [ "$serviceType" == "stpfn" ]
    then
        # create or update step function instance using sam
        sam deploy -t $layer/$stackName.yml \
            --stack-name $stackName-$environment \
            --s3-bucket $commonS3Bucket \
            --s3-prefix $serviceType/scripts/stacks/$stackName \
            --parameter-overrides Entity=$entity Environment=$environment \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM \
            --region $region \
            --no-fail-on-empty-changeset
        
    elif [ "$serviceType" == "rle" ]
    then
        # create or update iam role instance using sam
        sam deploy -t $layer/$stackName.yml \
            --stack-name $stackName-$environment \
            --s3-bucket $commonS3Bucket \
            --s3-prefix $serviceType/scripts/stacks/$stackName \
            --parameter-overrides Entity=$entity Environment=$environment \
                DaasCoreAccountId=$daasCoreAccountId DaasCoreEntity=$daasCoreEntity \
            --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM CAPABILITY_IAM \
            --region $region \
            --no-fail-on-empty-changeset

    else
        # create or update default (catch all) service using sam
        sam deploy -t $layer/$stackName.yml \
            --stack-name $stackName-$environment \
            --s3-bucket $commonS3Bucket \
            --s3-prefix $serviceType/scripts/stacks/$stackName \
            --parameter-overrides Entity=$entity Environment=$environment Region=$region \
            --capabilities CAPABILITY_AUTO_EXPAND \
            --region $region \
            --no-fail-on-empty-changeset 

    fi
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <accountid> <region> <environment> <service type> <application> <<lambda version>>"
fi