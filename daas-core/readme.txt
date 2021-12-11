#  -------------------------------------------------------
#  File Name: readme.txt
#  Description: Purpose of this file is to help fellow developers understand the objects in this repository and provide helpful hints.
#  Programmer:  Ganesh Nathan
#  Date:        11/19/2021
#  -------------------------------------------------------

1) daas-client1-stk-vpc-common-daas.yml
This stack yaml file will be responsible to deploy the vpc in AWS CloudFormation. This template will be called externally for all
operations (create/update/delete).

2) create-stack (.bat/.sh)
This file will create the vpc stack. This file takes 2 Parameters - Environment and Region.

3) delete-stack (.bat/.sh)
This file will  delete the vpc stack. This file takes 1 Parameters - Environment.

4) deploy-vpc (.bat/.sh)
Deploys the vpc stack. This file takes 2 Parameters - Environment and Region. NOTE: Although this file can be run standalone,
it is embedded in create-stack and update-stack batch files. Running this will ensure the latest file in the local drive is uploaded to the common folder.

7) update-stack.bat (.bat/.sh)
This file will update the vpc stack. NOTE: This can be run any number of times. There is no limit. This file takes
2 Parameters - Environment and Region.

Steps for Updating:
If changes needed to be made to the stack, please follow below steps:
1) Open the daas-client1-stk-vpc-common-daas.yml file in your favorite editor and make the necessary change.
2) Run the update-stack batch file providing the environment, region. NOTE: you cannot run the create-stack batch file since the object is already created.

Steps for Cloning:
1) Clone the repository in your local drive.
2) Edit the daas-client1-stk-vpc-common-daas.yml file and make the following changes:
   a) Update the BastionHostKeyName Parameter.
   b) Update the Name Parameter.
   c) Determine the number of Private and Public Subnets neeeded and enable them in the file.
      i) set the value to true for the subnet
      ii) set the cidr range
      iii) set the AZ region
   d) Determine if IGW is needed and set the Parameter.
   e) Update the VpcCidrBlock Parameter.
