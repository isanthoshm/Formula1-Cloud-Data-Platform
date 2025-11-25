Project Description:

The Formula1 Cloud Data Platform project is an end-to-end data engineering solution designed to demonstrate modern data analytics architecture on Microsoft Azure. The project leverages Azure Databricks, Azure Data Lake Storage Gen2, and Azure Data Factory to ingest, transform, and analyze real-world Formula1 racing data from the Ergast API.

The project follows a multi-layered data lake architecture — Raw, Processed, and Presentation layers — to ensure data quality, scalability, and efficient data management. Using Databricks notebooks (PySpark and Spark SQL), data is ingested from multiple sources (CSV and JSON), cleaned, enriched with audit columns, and stored in Parquet/Delta format for optimized performance and ACID compliance.

Azure Data Factory orchestrates the data pipelines for automated and scheduled execution, while Delta Lake enables incremental data loads, versioning, and time travel for historical analysis. Unity Catalog is implemented to manage data governance, access control, and lineage across multiple workspaces.

In the final stage, the curated data is visualized and analyzed to identify dominant drivers and teams, providing valuable insights into Formula1 performance trends.
