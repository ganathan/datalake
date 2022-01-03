DaaS-Core consists of core services deployed in an AWS Account. 

1) deploy-daas-core (.bat/.sh)
This is the script file to deploy DaaS-Core. The script file requires 4 parameteres: 

   a) Entity (this is the name of the organization).
   b) AccountId (this is the AWS Account ID where daas-core is targeted to be deployed).
   c) Region (this is the AWS region where daas-core is targeted to be deployed. Example: us-west-2. Please review AWS documentation on valid regions).
   d) Environment (this is the environment where daas-core is targeted to be deployed. Valid values are - poc, dev, tst, uat, sit, prd).