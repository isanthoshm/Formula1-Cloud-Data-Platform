import org.apache.spark.sql.*;
import org.apache.spark.sql.types.*;
import static org.apache.spark.sql.functions.*;

public class IngestCircuits {
    public static void main(String[] args) {

        // Initialize Spark Session
        SparkSession spark = SparkSession.builder()
                .appName("IngestCircuits")
                .getOrCreate();

        // Parameters (In Java, these usually come from Spark Config or Args)
        String vDataSource = spark.conf().get("p_data_source", "");
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");
        
        // Paths from your configuration
        String rawFolderPath = "wasbs://raw@formula420.blob.core.windows.net";

        // ##### Step 1 - Define Schema
        StructType circuitsSchema = new StructType(new StructField[]{
                DataTypes.createStructField("circuitId", DataTypes.IntegerType, false),
                DataTypes.createStructField("circuitRef", DataTypes.StringType, true),
                DataTypes.createStructField("name", DataTypes.StringType, true),
                DataTypes.createStructField("location", DataTypes.StringType, true),
                DataTypes.createStructField("country", DataTypes.StringType, true),
                DataTypes.createStructField("lat", DataTypes.DoubleType, true),
                DataTypes.createStructField("lng", DataTypes.DoubleType, true),
                DataTypes.createStructField("alt", DataTypes.IntegerType, true),
                DataTypes.createStructField("url", DataTypes.StringType, true)
        });

        // Read CSV file
        Dataset<Row> circuitsDf = spark.read()
                .option("header", true)
                .schema(circuitsSchema)
                .csv(rawFolderPath + "/" + vFileDate + "/circuits.csv");

        // ##### Step 2 & 3 - Select and Rename Columns
        Dataset<Row> circuitsRenamedDf = circuitsDf.select(
                col("circuitId").as("circuit_id"),
                col("circuitRef").as("circuit_ref"),
                col("name"),
                col("location"),
                col("country"),
                col("lat").as("latitude"),
                col("lng").as("longitude"),
                col("alt").as("altitude")
        )
        .withColumn("data_source", lit(vDataSource))
        .withColumn("file_date", lit(vFileDate));

        // ##### Step 4 - Add ingestion date (Using your common utility)
        Dataset<Row> circuitsFinalDf = SparkUtils.addIngestionDate(circuitsRenamedDf);

        // ##### Step 5 - Write to Delta Table
        circuitsFinalDf.write()
                .mode("overwrite")
                .format("delta")
                .saveAsTable("f1_processed.circuits");

        System.out.println("Circuits Ingestion Successful");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest circuits.csv file

# COMMAND ----------

dbutils.widgets.text("p_data_source", "")
v_data_source = dbutils.widgets.get("p_data_source")

# COMMAND ----------

dbutils.widgets.text("p_file_date", "2021-03-21")
v_file_date = dbutils.widgets.get("p_file_date")

# COMMAND ----------

# MAGIC %run "../includes/configuration"

# COMMAND ----------

# MAGIC %run "../includes/common_functions"

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 1 - Read the CSV file using the spark dataframe reader

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

# COMMAND ----------

circuits_schema = StructType(fields=[StructField("circuitId", IntegerType(), False),
                                     StructField("circuitRef", StringType(), True),
                                     StructField("name", StringType(), True),
                                     StructField("location", StringType(), True),
                                     StructField("country", StringType(), True),
                                     StructField("lat", DoubleType(), True),
                                     StructField("lng", DoubleType(), True),
                                     StructField("alt", IntegerType(), True),
                                     StructField("url", StringType(), True)
])

# COMMAND ----------

circuits_df = spark.read \
.option("header", True) \
.schema(circuits_schema) \
.csv(f"{raw_folder_path}/{v_file_date}/circuits.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2 - Select only the required columns

# COMMAND ----------

from pyspark.sql.functions import col

# COMMAND ----------

circuits_selected_df = circuits_df.select(col("circuitId"), col("circuitRef"), col("name"), col("location"), col("country"), col("lat"), col("lng"), col("alt"))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3 - Rename the columns as required

# COMMAND ----------

from pyspark.sql.functions import lit

# COMMAND ----------

circuits_renamed_df = circuits_selected_df.withColumnRenamed("circuitId", "circuit_id") \
.withColumnRenamed("circuitRef", "circuit_ref") \
.withColumnRenamed("lat", "latitude") \
.withColumnRenamed("lng", "longitude") \
.withColumnRenamed("alt", "altitude") \
.withColumn("data_source", lit(v_data_source)) \
.withColumn("file_date", lit(v_file_date))

# COMMAND ----------

# MAGIC %md 
# MAGIC ##### Step 4 - Add ingestion date to the dataframe

# COMMAND ----------

circuits_final_df = add_ingestion_date(circuits_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 5 - Write data to datalake as parquet

# COMMAND ----------

circuits_final_df.write.mode("overwrite").format("delta").saveAsTable("f1_processed.circuits")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_processed.circuits;

# COMMAND ----------

dbutils.notebook.exit("Success")
