# datalake
Data lake as a service (DaaS) is a fedarated data lake solution. Corporations have mutliple departments and each department tends to host their data in a data lake owned by them. Although creating a single data lake for the enterprise is ideal, but is almost always a challenging task. 

Having multiple data lakes provides flexibility in data ownership and access control. However introduces complexity in Governance and enforcing Standards. DaaS provides a flexible federated model where the DaaS-Core is deployed in a centralized AWS account, owned by a shared services team or an Corporate IT, Governance team. While the DaaS-Client is deployed for one or more departments in their repective AWS account. 

DaaS is also flexible to deploy both the Core and the Client in the same AWS Account, to help have a single data lake for the entire organization if needed.

# Architecture


# Core Components

DaaS Core support 2 or more layers in a DaaS Client data lake. At a minimum a DaaS Client should have the Ingestion Layer and the Distribution Layer. A typical data lake has 3 layers. Ingestion, Curation and Distribution. Some data lakes have Ingestion, Curation, Refine, Distribution layers. There is no limit on the layers one could have in DaaS Client.

Ingestion Layer is used to ingest data from various sources. It is a central repository for all the data for the department(s)/Organization. Data is ingested in the raw format. Optionally, can be configured to convert the format. For example Microsft Excel file can be ingested and DaaS Core can convert it to CSV. XML file can be ingested and DaaS Core can convert it to Json. 

## Ingestion Flow
Following is the ingestion flow for DaaS Core.

DaaS Core deploys a Ingestion Queue to allow clients notify all data ingested in their respective S3 buckets. The Queue tracks all creates and for each create notification invokes a Ingestion Step Function. 

The Step Function optionally converts file (if needed) and invokes the Ingestion metadata generator for each notification. The metadata generator creates a Ingestion Glue Database and a Glue Craweler (if not already exists) for the data set. Once created, the crawler is started to create the Glue Catalog. The Catalog is registed to Lake Formation to allow the data stewards to define Access Control.

A Ingestion Event Rule is created that monitors the Crawler status and optionally  invokes a Ingestion profiler step function that profiles and classifies the data. At this point the Glue Database has the dataset as a table that can be quried via Athena or any JDBC/OBDC compliant SQL editor and each column in the dataset has classification and profile information.

DaaS ingestion layer is not designed for applying business rules or transformations. This is performed in the Curation Layer of the data lake. Typically a data modeller would model the data and add business rules to validate and tarnsform the data. Any integration tool can be used for the curation layer.

DaaS supports DBT (Data Build Tool) to build the model and transformations in the curation layer if needed. Please note DBT is optional any tool can be used like Informatica, Matellion, Snaplogic, etc.. Since the curation layer is optional, the data team can transform the data on the fly and persist the curated data in the distrbution layer. 

When data team decides to use the Curation Layer, Daas Core deploys a Curation Queue to help create Glue Catalog (similar to the ingestion layer) and registers in lake formation for data stewards to build access control. If the data team uses DBT daas deploys Aurora postgres database to auto replicate ingestion data into the raw layer in the postgress database.

Data modelers can build their model in Kimball, Inmonn, 3NF, Data Vault 2.0 etc and persist the model. DaaS scans the model and generates the tables and executes DBT framework to deploy the model. Please review my blog on Data Warehouse Automation that goes over this feature in detail.

Once data is persisted in distribution layer, DaaS Core deploys a Distribution Queue to create the Glue Catalog and registers the data in Lake Formation for data stewards to define access control.

DaaS optionally supports 8 channels of distribution:
Data can be published as an Api (REST Api) DaaS Core deploys API Gateway for the data and associated lambda and enforces Lake Formation access control.
Data can be published to allow reporting tools like Tableau, Microstrategy, Looker, QlikView, Power BI, etc.. to build custom reports and Dashboards. DaaS publishes jdbc/obdc connection url and deploys necessary access controls via Lake Formation. 
Data can be published as a Topic for subscibers to get notified of the data. DaaS deploys necessary access controls via Lake Formation.
Data can be published as a message in a Queue for consumers to ingest the message. DaaS deploys necessary access controls via Lake Formation.
Data can be streamed. DaaS deploys necessary access controls via Lake Formation.
Data can be published as an SDK for data teams to build custom applications. DaaS deploys necessary access controls via Lake Formation.
Data can be Queried directly via Athena. DaaS deploys necessary access controls via Lake Formation.
Data can be directly access as a file via SFTP. DaaS deploys necessary access controls via Lake Formation.



