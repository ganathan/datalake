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
SET stackName=stk-%serviceType%-%application%
SET commonS3Folder=%entity%-s3-%accountId%-%region%-common-artifacts-%environment%


REM Copy the Stack to the common deploy folder
call aws s3 cp .\%application%\%stackName%.yml ^
   s3://%commonS3Folder%/%serviceType%-stack/scripts/stacks/%stackName%.yml
goto eof

REM Copy the lamdba environment variable to the common deploy folder
if serviceType==lmd
   call aws s3 cp .\%application%\%stackName%-env-var.yml ^
      s3://%commonS3Folder%/%objectType%/scripts/stacks/%stackName%-env-var.yml
goto eof

:usage
@echo ERROR: Missing Required Parameters! Please see below the syntax to execute this batch file.
@echo USAGE: "%0 <entity> <account id> <environment> <region> <service type>"

:eof
@echo Done!
