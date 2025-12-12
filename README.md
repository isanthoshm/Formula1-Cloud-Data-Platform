# Formula 1 Cloud Data Platform
## 1. Project Title & Introduction

One-Liner: A complete, end-to-end Data Lakehouse solution built on Azure and Databricks to analyze Formula 1 historical performance and identify dominant drivers/teams.

Goal: To establish a single source of truth for F1 data and compute key analytical metrics, like Average Points per Race, for historical dominance analysis.

## 2. Architecture & Technology Stack
Use a simple table or list to highlight the core technologies
| Component | Technology | Purpose in Project |
| :--- | :--- | :--- |
| **Cloud Platform** | Azure | Infrastructure hosting (ADLS, ADF, Databricks). |
| **Storage** | Azure Data Lake Storage (ADLS) | Multi-layered storage for Raw, Processed, and Presentation data. |
| **Processing** | Azure Databricks (PySpark) | Scalable data transformation and modeling. |
| **Data Format** | **Delta Lake** | Ensures ACID transactions, schema enforcement, and versioning across all data layers. |
| **Orchestration** | **Azure Data Factory (ADF)** | Triggers the Databricks notebooks and manages the incremental pipeline flow. |
| **Data Source** | Ergast API  | Raw Formula 1 race data. |

## 3. Data Flow and Layers (The Lakehouse)
Briefly describe the three layers using the common Lakehouse terminology.
| Layer | Database/Location | Key Activity | Output | 
| :--- | :--- | :--- |:--- |
| **Bronze (Raw)** | ADLS/raw | Landing raw data. | Unmodified source data. |
| **Silver (Processed)** | f1_processed | Data cleaning, standardization, and column renaming (e.g., driverId to driver_id). | Clean, normalized tables (circuits, drivers, results, etc.). |
| **Gold (Presentation)** | f1_presentation | Data modeling, joins, aggregation, and creation of analytical fact tables. | High-value tables: calculated_race_results, driver_standings, constructor_standings. |

## 4. Key Engineering Features
Highlight what makes your solution robust and professional.

Incremental Loading (Upserts): Implemented using Delta Lake's MERGE INTO command (via the merge_delta_data function) to efficiently handle new and updated race results without full reprocessing.

Pipeline Orchestration: ADF is used to manage notebook execution and pass dynamic parameters like the p_file_date for targeted, efficient processing.

Parameterization: All notebooks are parameterized to accept source and file date variables, allowing for flexible, reproducible runs.

Custom Metrics: Creation of the calculated_points metric (11 - position) to normalize F1 scoring across historical rule changes, enabling a truly fair dominance analysis.

## 5. Analysis & Results
Showcase the output that the pipeline is designed to generate.

Metric: Ranking based on Average Points per Race (calculated from the Gold layer).

Queries: SQL scripts are provided to find dominant entities across all-time, 2011-2020, and 2001-2010 eras.

Visualization Prep: Uses Window Functions (RANK() OVER) to select the top entities (Top 10 Drivers / Top 5 Teams) for time-series visualization in BI tools.

