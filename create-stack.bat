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
SET lambdaVersion=%7
SET stackName=stk-%serviceType%-%application%
SET commonS3Folder=%entity%-s3-%accountId%-%region%-common-artifacts-%environment%


REM Deploy the stack first
call %application%\deploy-%serviceType%.bat %entity% %accountId% %application% %environment% %region% %serviceType% %lambdaVersion%

aws cloudformation create-stack ^
   --stack-name %stackName%-%environment% ^
	 --region %region% ^
	 --template-url https://s3-%region%.amazonaws.com/%commonS3Folder%/%serviceType%/scripts/stacks/%stackName%/%stackName%.yml ^
	 --parameters ParameterKey=Environment,ParameterValue=%environment%
goto eof

:usage
@echo ERROR: Missing Required Parameters! Please see below the syntax to execute this batch file.
@echo USAGE: "%0 <entity> <account id> <application> <environment> <region> <service type>"

:eof
@echo Done!
