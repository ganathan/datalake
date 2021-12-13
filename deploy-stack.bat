@echo off
REM Check if parameters are defined
if [%1]==[] goto usage
if [%2]==[] goto usage
if [%3]==[] goto usage
if [%4]==[] goto usage
if [%5]==[] goto usage
if [%6]==[] goto usage

REM Set variables
SET entity=%1
SET accountId=%2
SET application=%3
SET environment=%4
SET region=%5
SET serviceType=%6
SET lambdaName=%7
SET lambdaVersion=%8
SET stackName=stk-%serviceType%-%application%
SET commonS3Folder=%entity%-s3-%accountId%-%region%-common-artifacts-%environment%
SET type="update"

REM Lambda service needs special handling...
if serviceType=="lmd"
   if [%8]==[]
         lambdaVersion=100
   REM reset variables for lambda
   SET stackName=stk-%serviceType%-%lambdaName%
   SET functionName=%serviceType%-%application%

   REM Compress lamdba source file
   powershell.exe Compress-Archive -LiteralPath ./%application%/%functionName%.py  -DestinationPath ./%application%/%functionName%-%lambdaVersion%.zip

   REM Copy zip file to common stack folder
   call aws s3 cp ./%application%/%functionName%-%version%.zip ^
      s3://%commonS3Folder%/%objectType%/scripts/stacks/%stackName%/%functionName%-%version%.zip

   REM Copy the env var file to the common stack folder
   call aws s3 cp ./%application%/%stackName%-env-var.yml  ^
      s3://%commonS3Folder%/%objectType%/scripts/stacks/%stackName%/%stackName%-env-var.yml


REM Copy the Stack to the common stack folder
call aws s3 cp .\%application%\%stackName%.yml ^
   s3://%commonS3Folder%/%serviceType%-stack/scripts/stacks/%stackName%.yml


stackStatus=$(aws s3api head-bucket --bucket "${commonS3Bucket}" 2>&1)
if echo "${stackStatus}" | grep 'not found';
type="create"

aws cloudformation %type%-stack ^
   --stack-name %stackName%-%environment% ^
	 --region %region% ^
	 --template-url https://s3-%region%.amazonaws.com/%commonS3Folder%/%serviceType%/scripts/stacks/%stackName%/%stackName%.yml ^
	 --parameters ParameterKey=Environment,ParameterValue=%environment%
goto eof

:usage
@echo ERROR: Missing Required Parameters! Please see below the syntax to execute this batch file.
@echo USAGE: "%0 <entity> <account id> <application> <environment> <region> <service type> <<lambda name>> <<lambda version>>"

:eof
@echo Done!
