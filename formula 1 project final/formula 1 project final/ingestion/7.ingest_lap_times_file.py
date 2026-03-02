import org.apache.spark.sql.*;
import org.apache.spark.sql.types.*;
import static org.apache.spark.sql.functions.*;

public class IngestLapTimes {
    public static void main(String[] args) {

        // Initialize Spark Session
        SparkSession spark = SparkSession.builder()
                .appName("IngestLapTimes")
                .getOrCreate();

        // Parameters
        String vDataSource = spark.conf().get("p_data_source", "");
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");
        String rawFolderPath = "wasbs://raw@formula420.blob.core.windows.net";
        String processedFolderPath = "wasbs://processed@formula420.blob.core.windows.net";

        // ##### Step 1 - Define Schema
        StructType lapTimesSchema = new StructType(new StructField[]{
                DataTypes.createStructField("raceId", DataTypes.IntegerType, false),
                DataTypes.createStructField("driverId", DataTypes.IntegerType, true),
                DataTypes.createStructField("lap", DataTypes.IntegerType, true),
                DataTypes.createStructField("position", DataTypes.IntegerType, true),
                DataTypes.createStructField("time", DataTypes.StringType, true),
                DataTypes.createStructField("milliseconds", DataTypes.IntegerType, true)
        });

        // Read the entire folder of CSV files
        // Spark automatically discovers all CSV files within the 'lap_times' directory
        Dataset<Row> lapTimesDf = spark.read()
                .schema(lapTimesSchema)
                .csv(rawFolderPath + "/" + vFileDate + "/lap_times");

        // ##### Step 2 - Rename Columns and Add Metadata
        Dataset<Row> finalDf = SparkUtils.addIngestionDate(lapTimesDf)
                .withColumnRenamed("driverId", "driver_id")
                .withColumnRenamed("raceId", "race_id")
                .withColumn("data_source", lit(vDataSource))
                .withColumn("file_date", lit(vFileDate));

        // ##### Step 3 - Delta Merge
        // Condition: Unique key is race_id, driver_id, and lap number
        String mergeCondition = "tgt.race_id = src.race_id AND " +
                                "tgt.driver_id = src.driver_id AND " +
                                "tgt.lap = src.lap";

        SparkUtils.mergeDeltaData(
            spark, 
            finalDf, 
            "f1_processed", 
            "lap_times", 
            processedFolderPath, 
            mergeCondition, 
            "race_id"
        );

        System.out.println("Lap Times Ingestion and Merge Successful");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest lap_times folder

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
# MAGIC ##### Step 1 - Read the CSV file using the spark dataframe reader API

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# COMMAND ----------

lap_times_schema = StructType(fields=[StructField("raceId", IntegerType(), False),
                                      StructField("driverId", IntegerType(), True),
                                      StructField("lap", IntegerType(), True),
                                      StructField("position", IntegerType(), True),
                                      StructField("time", StringType(), True),
                                      StructField("milliseconds", IntegerType(), True)
                                     ])

# COMMAND ----------

lap_times_df = spark.read \
.schema(lap_times_schema) \
.csv(f"{raw_folder_path}/{v_file_date}/lap_times")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2 - Rename columns and add new columns
# MAGIC 1. Rename driverId and raceId
# MAGIC 1. Add ingestion_date with current timestamp

# COMMAND ----------

lap_times_with_ingestion_date_df = add_ingestion_date(lap_times_df)

# COMMAND ----------

from pyspark.sql.functions import lit

# COMMAND ----------

final_df = lap_times_with_ingestion_date_df.withColumnRenamed("driverId", "driver_id") \
.withColumnRenamed("raceId", "race_id") \
.withColumn("ingestion_date", current_timestamp()) \
.withColumn("data_source", lit(v_data_source)) \
.withColumn("file_date", lit(v_file_date))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3 - Write to output to processed container in parquet format

# COMMAND ----------

#overwrite_partition(final_df, 'f1_processed', 'lap_times', 'race_id')

# COMMAND ----------

merge_condition = "tgt.race_id = src.race_id AND tgt.driver_id = src.driver_id AND tgt.lap = src.lap AND tgt.race_id = src.race_id"
merge_delta_data(final_df, 'f1_processed', 'lap_times', processed_folder_path, merge_condition, 'race_id')

# COMMAND ----------

dbutils.notebook.exit("Success")
