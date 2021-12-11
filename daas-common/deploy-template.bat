@echo off
REM Check if parameters are defined
if [%1]==[] goto usage
if [%2]==[] goto usage
if [%3]==[] goto usage
if [%4]==[] goto usage

REM Set variables
SET entity=%1
SET environment=%2
SET region=%3
SET serviceType=%4
SET stackName=cft-%serviceType%-common-template
SET commonS3Folder=%entity%-s3-%region%-common-artifacts-%environment%


REM Copy the Stack to the common deploy folder
call aws s3 cp .\%stackName%.yml ^
   s3://%commonS3Folder%/%serviceType%/scripts/template/%stackName%.yml
goto eof

:usage
@echo ERROR: Missing Required Parameters! Please see below the syntax to execute this batch file.
@echo USAGE: "%0 <entity> <environment> <region> <service type>"

:eof
@echo Done!
