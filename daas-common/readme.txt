Common template for each AWS service. This is the parent stack in the CloudFormation
nested stack hierarchy. NOTE: The common template is created at an account level
and reused across multiple applications/projects. 

This facitilites governance and allows to establish standards across services.

1) deploy-template (.bat/.sh)
Copies the common deployment file to the common s3 folder. This file takes 5 Parameters - Enity, Account Id, Environment, Region and Service Type. Running this will
ensure the latest file in the local drive is uploaded to the common folder.

2) cft-"Service Type"-common-template.yml (NOTE: Service Type)
This is the parent template yaml file that is responsible to deploy the appropriate service in AWS CloudFormation. This template will be called externally for all
operations (create/update/delete). It is one per AWS service. 

NOTE: This file should not be cloned. Take extreme caution when updating the file. Any change done to the template will have cascading impact
on all deployed service for the given environment.

Steps for deploying:
--------------------
1) Open command prompt and execute the deploy-template file. 
Example Syntax: "deploy-template.bat myorg myaccountid dev us-west-2 vpc" (windows) "./deploy-template.sh myorg myaccountid dev us-west-2 vpc" (linux/mac)
The above example is for deploying a VPC in the AWS Account. The same syntax is for all aws services.

Steps for updating:
-------------------
1) Open the cft-"service type"-common-template.yml file in your favorite text editor and make the necessary change.
2) Run the deploy-template batch file providing the entity, account id, environment, region and service type.

Steps for cloning:
------------------
The common template is one to one for a given aws service. It should not be cloned. 
You can have only one common template per service. Only updates can be made to the specific
service type common template.
