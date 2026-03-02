import org.apache.spark.sql.*;
import org.apache.spark.sql.types.*;
import static org.apache.spark.sql.functions.*;

public class IngestRaces {
    public static void main(String[] args) {

        // Initialize Spark Session
        SparkSession spark = SparkSession.builder()
                .appName("IngestRaces")
                .getOrCreate();

        // Parameters
        String vDataSource = spark.conf().get("p_data_source", "");
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");
        String rawFolderPath = "wasbs://raw@formula420.blob.core.windows.net";

        // ##### Step 1 - Define Schema
        StructType racesSchema = new StructType(new StructField[]{
                DataTypes.createStructField("raceId", DataTypes.IntegerType, false),
                DataTypes.createStructField("year", DataTypes.IntegerType, true),
                DataTypes.createStructField("round", DataTypes.IntegerType, true),
                DataTypes.createStructField("circuitId", DataTypes.IntegerType, true),
                DataTypes.createStructField("name", DataTypes.StringType, true),
                DataTypes.createStructField("date", DataTypes.DateType, true),
                DataTypes.createStructField("time", DataTypes.StringType, true),
                DataTypes.createStructField("url", DataTypes.StringType, true)
        });

        // Read CSV
        Dataset<Row> racesDf = spark.read()
                .option("header", true)
                .schema(racesSchema)
                .csv(rawFolderPath + "/" + vFileDate + "/races.csv");

        // ##### Step 2 - Add Metadata and Timestamp
        // In Java, use to_timestamp with explicit column concatenation
        Dataset<Row> racesWithTimestampDf = racesDf
                .withColumn("race_timestamp", to_timestamp(concat(col("date"), lit(" "), col("time")), "yyyy-MM-dd HH:mm:ss"))
                .withColumn("data_source", lit(vDataSource))
                .withColumn("file_date", lit(vFileDate));

        // Add ingestion date using our SparkUtils helper
        Dataset<Row> racesWithIngestionDateDf = SparkUtils.addIngestionDate(racesWithTimestampDf);

        // ##### Step 3 - Select and Rename Columns
        Dataset<Row> racesFinalDf = racesWithIngestionDateDf.select(
                col("raceId").as("race_id"),
                col("year").as("race_year"),
                col("round"),
                col("circuitId").as("circuit_id"),
                col("name"),
                col("ingestion_date"),
                col("race_timestamp")
        );

        // ##### Step 4 - Write to Delta with Partitioning
        racesFinalDf.write()
                .mode("overwrite")
                .partitionBy("race_year") // Crucial for performance on large datasets
                .format("delta")
                .saveAsTable("f1_processed.races");

        System.out.println("Races Ingestion Successful");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest races.csv file

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

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType

# COMMAND ----------

races_schema = StructType(fields=[StructField("raceId", IntegerType(), False),
                                  StructField("year", IntegerType(), True),
                                  StructField("round", IntegerType(), True),
                                  StructField("circuitId", IntegerType(), True),
                                  StructField("name", StringType(), True),
                                  StructField("date", DateType(), True),
                                  StructField("time", StringType(), True),
                                  StructField("url", StringType(), True) 
])

# COMMAND ----------

races_df = spark.read \
.option("header", True) \
.schema(races_schema) \
.csv(f"{raw_folder_path}/{v_file_date}/races.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2 - Add ingestion date and race_timestamp to the dataframe

# COMMAND ----------

from pyspark.sql.functions import to_timestamp, concat, col, lit

# COMMAND ----------

races_with_timestamp_df = races_df.withColumn("race_timestamp", to_timestamp(concat(col('date'), lit(' '), col('time')), 'yyyy-MM-dd HH:mm:ss')) \
.withColumn("data_source", lit(v_data_source)) \
.withColumn("file_date", lit(v_file_date))

# COMMAND ----------

races_with_ingestion_date_df = add_ingestion_date(races_with_timestamp_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3 - Select only the columns required & rename as required

# COMMAND ----------

races_selected_df = races_with_ingestion_date_df.select(col('raceId').alias('race_id'), col('year').alias('race_year'), 
                                                   col('round'), col('circuitId').alias('circuit_id'),col('name'), col('ingestion_date'), col('race_timestamp'))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Write the output to processed container in parquet format

# COMMAND ----------

races_selected_df.write.mode("overwrite").partitionBy('race_year').format("delta").saveAsTable("f1_processed.races")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_processed.races;

# COMMAND ----------

dbutils.notebook.exit("Success")
