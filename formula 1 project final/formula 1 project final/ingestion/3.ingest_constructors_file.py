import org.apache.spark.sql.*;
import org.apache.spark.sql.types.*;
import static org.apache.spark.sql.functions.*;

public class IngestConstructors {
    public static void main(String[] args) {

        // Initialize Spark Session
        SparkSession spark = SparkSession.builder()
                .appName("IngestConstructors")
                .getOrCreate();

        // Parameters
        String vDataSource = spark.conf().get("p_data_source", "");
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");
        String rawFolderPath = "wasbs://raw@formula420.blob.core.windows.net";

        // ##### Step 1 - Define Schema
        // You can use a DDL string in Java too: 
        // String constructorsSchemaDDL = "constructorId INT, constructorRef STRING, name STRING, nationality STRING, url STRING";
        
        StructType constructorsSchema = new StructType(new StructField[]{
                DataTypes.createStructField("constructorId", DataTypes.IntegerType, false),
                DataTypes.createStructField("constructorRef", DataTypes.StringType, true),
                DataTypes.createStructField("name", DataTypes.StringType, true),
                DataTypes.createStructField("nationality", DataTypes.StringType, true),
                DataTypes.createStructField("url", DataTypes.StringType, true)
        });

        // Read JSON file
        Dataset<Row> constructorDf = spark.read()
                .schema(constructorsSchema)
                .json(rawFolderPath + "/" + vFileDate + "/constructors.json");

        // ##### Step 2 - Drop unwanted columns
        Dataset<Row> constructorDroppedDf = constructorDf.drop("url");

        // ##### Step 3 - Rename columns and add Metadata
        Dataset<Row> constructorRenamedDf = constructorDroppedDf
                .withColumnRenamed("constructorId", "constructor_id")
                .withColumnRenamed("constructorRef", "constructor_ref")
                .withColumn("data_source", lit(vDataSource))
                .withColumn("file_date", lit(vFileDate));

        // Add ingestion date using our SparkUtils helper
        Dataset<Row> constructorFinalDf = SparkUtils.addIngestionDate(constructorRenamedDf);

        // ##### Step 4 - Write to Delta Table
        constructorFinalDf.write()
                .mode("overwrite")
                .format("delta")
                .saveAsTable("f1_processed.constructors");

        System.out.println("Constructors Ingestion Successful");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest constructors.json file

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
# MAGIC ##### Step 1 - Read the JSON file using the spark dataframe reader

# COMMAND ----------

constructors_schema = "constructorId INT, constructorRef STRING, name STRING, nationality STRING, url STRING"

# COMMAND ----------

constructor_df = spark.read \
.schema(constructors_schema) \
.json(f"{raw_folder_path}/{v_file_date}/constructors.json")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2 - Drop unwanted columns from the dataframe

# COMMAND ----------

from pyspark.sql.functions import col

# COMMAND ----------

constructor_dropped_df = constructor_df.drop(col('url'))

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3 - Rename columns and add ingestion date

# COMMAND ----------

from pyspark.sql.functions import lit

# COMMAND ----------

constructor_renamed_df = constructor_dropped_df.withColumnRenamed("constructorId", "constructor_id") \
                                             .withColumnRenamed("constructorRef", "constructor_ref") \
                                             .withColumn("data_source", lit(v_data_source)) \
                                             .withColumn("file_date", lit(v_file_date))

# COMMAND ----------

constructor_final_df = add_ingestion_date(constructor_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 4 Write output to parquet file

# COMMAND ----------

constructor_final_df.write.mode("overwrite").format("delta").saveAsTable("f1_processed.constructors")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_processed.constructors;

# COMMAND ----------

dbutils.notebook.exit("Success")
