@echo off
REM Check if parameters are defined
if [%1]==[] goto usage
if [%2]==[] goto usage
if [%3]==[] goto usage
if [%4]==[] goto usage



REM Check if parameters are defined
SET application=%1
SET environment=%2
SET region=%3
SET serviceType=%4
SET stackName=stk-%serviceType%-%application%


REM Delete the stack
call aws cloudformation delete-stack ^
          --stack-name %stackName%-%environment% ^
      		--region %region%
goto eof

:usage
@echo ERROR: Missing Required Parameters! Please see below the syntax to execute this batch file.
@echo USAGE: "%0 <application> <environment> <region> <service type>"

:eof
@echo Done!
