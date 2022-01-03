DaaS-Client consists of client services deployed in an AWS Account. These services can be deployed in the daas-client deployed AWS Account or in seperate AWS Accounts. An organization can have any 1 or more DaaS-Client deployments. 


1) deploy-daas-client (.bat/.sh)
This is the script file to deploy DaaS-Client. The script file requires 4 parameteres: 

   a) Entity (this is the name of the organization).
   b) AccountId (this is the AWS Account ID where daas-client is targeted to be deployed).
   c) Region (this is the AWS region where daas-client is targeted to be deployed. Example: us-west-2. Please review AWS documentation on valid regions).
   d) Environment (this is the environment where daas-client is targeted to be deployed. Valid values are - poc, dev, tst, uat, sit, prd).