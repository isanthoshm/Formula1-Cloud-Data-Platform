import org.apache.spark.sql.*;
import org.apache.spark.sql.types.*;
import static org.apache.spark.sql.functions.*;

public class IngestDrivers {
    public static void main(String[] args) {

        // Initialize Spark Session
        SparkSession spark = SparkSession.builder()
                .appName("IngestDrivers")
                .getOrCreate();

        // Parameters
        String vDataSource = spark.conf().get("p_data_source", "");
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");
        String rawFolderPath = "wasbs://raw@formula420.blob.core.windows.net";

        // ##### Step 1 - Define Nested Schemas
        // Inner schema for the 'name' object
        StructType nameSchema = new StructType(new StructField[]{
                DataTypes.createStructField("forename", DataTypes.StringType, true),
                DataTypes.createStructField("surname", DataTypes.StringType, true)
        });

        // Main schema for drivers.json
        StructType driversSchema = new StructType(new StructField[]{
                DataTypes.createStructField("driverId", DataTypes.IntegerType, false),
                DataTypes.createStructField("driverRef", DataTypes.StringType, true),
                DataTypes.createStructField("number", DataTypes.IntegerType, true),
                DataTypes.createStructField("code", DataTypes.StringType, true),
                DataTypes.createStructField("name", nameSchema, true), // Nesting the nameSchema here
                DataTypes.createStructField("dob", DataTypes.DateType, true),
                DataTypes.createStructField("nationality", DataTypes.StringType, true),
                DataTypes.createStructField("url", DataTypes.StringType, true)
        });

        // Read Nested JSON file
        Dataset<Row> driversDf = spark.read()
                .schema(driversSchema)
                .json(rawFolderPath + "/" + vFileDate + "/drivers.json");

        // ##### Step 2 - Transform and Add Columns
        // Use concat and dot notation to flatten the name object
        Dataset<Row> driversWithColumnsDf = SparkUtils.addIngestionDate(driversDf)
                .withColumnRenamed("driverId", "driver_id")
                .withColumnRenamed("driverRef", "driver_ref")
                .withColumn("name", concat(col("name.forename"), lit(" "), col("name.surname")))
                .withColumn("data_source", lit(vDataSource))
                .withColumn("file_date", lit(vFileDate));

        // ##### Step 3 - Drop Unwanted Columns
        Dataset<Row> driversFinalDf = driversWithColumnsDf.drop("url");

        // ##### Step 4 - Write to Delta Table
        driversFinalDf.write()
                .mode("overwrite")
                .format("delta")
                .saveAsTable("f1_processed.drivers");

        System.out.println("Drivers Ingestion and Flattening Successful");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest drivers.json file

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
# MAGIC ##### Step 1 - Read the JSON file using the spark dataframe reader API

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType

# COMMAND ----------

name_schema = StructType(fields=[StructField("forename", StringType(), True),
                                 StructField("surname", StringType(), True)
  
])

# COMMAND ----------

drivers_schema = StructType(fields=[StructField("driverId", IntegerType(), False),
                                    StructField("driverRef", StringType(), True),
                                    StructField("number", IntegerType(), True),
                                    StructField("code", StringType(), True),
                                    StructField("name", name_schema),
                                    StructField("dob", DateType(), True),
                                    StructField("nationality", StringType(), True),
                                    StructField("url", StringType(), True)  
])

# COMMAND ----------

drivers_df = spark.read \
.schema(drivers_schema) \
.json(f"{raw_folder_path}/{v_file_date}/drivers.json")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2 - Rename columns and add new columns
# MAGIC 1. driverId renamed to driver_id  
# MAGIC 1. driverRef renamed to driver_ref  
# MAGIC 1. ingestion date added
# MAGIC 1. name added with concatenation of forename and surname

# COMMAND ----------

from pyspark.sql.functions import col, concat, lit

# COMMAND ----------

drivers_with_ingestion_date_df = add_ingestion_date(drivers_df)

# COMMAND ----------

drivers_with_columns_df = drivers_with_ingestion_date_df.withColumnRenamed("driverId", "driver_id") \
                                    .withColumnRenamed("driverRef", "driver_ref") \
                                    .withColumn("name", concat(col("name.forename"), lit(" "), col("name.surname"))) \
                                    .withColumn("data_source", lit(v_data_source)) \
                                    .withColumn("file_date", lit(v_file_date))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3 - Drop the unwanted columns
# MAGIC 1. name.forename
# MAGIC 1. name.surname
# MAGIC 1. url

# COMMAND ----------

drivers_final_df = drivers_with_columns_df.drop(col("url"))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 4 - Write to output to processed container in parquet format

# COMMAND ----------

drivers_final_df.write.mode("overwrite").format("delta").saveAsTable("f1_processed.drivers")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_processed.drivers

# COMMAND ----------

dbutils.notebook.exit("Success")
