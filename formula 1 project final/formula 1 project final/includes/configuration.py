import org.apache.spark.sql.SparkSession;
import org.apache.hadoop.conf.Configuration;

public class SparkConfig {

    // Storage Paths - In Java, we typically use 'final' constants for these
    public static final String RAW_FOLDER_PATH = "wasbs://raw@formula420.blob.core.windows.net";
    public static final String PROCESSED_FOLDER_PATH = "wasbs://processed@formula420.blob.core.windows.net";
    public static final String PRESENTATION_FOLDER_PATH = "wasbs://presentation@formula420.blob.core.windows.net";

    /**
     * Initializes a SparkSession with Azure Blob Storage credentials.
     * In a Java project, this centralizes your connection logic.
     */
    public static SparkSession getSparkSession() {
        SparkSession spark = SparkSession.builder()
                .appName("Formula1DataEngineering")
                .getOrCreate();

        // Access the underlying Hadoop configuration to set Azure credentials
        Configuration conf = spark.sparkContext().hadoopConfiguration();
        conf.set("fs.azure.account.key.formula420.blob.core.windows.net", 
                 "s3f9bzNCqGGaSwqdpSFoofwcaxncyGe6dxcIFj9u2hrbxyyTx2nzG25kV3JYh+5QLERrIE0ZTDjZ+ASthbsy5w==");

        return spark;
    }
}

# Databricks notebook source
spark.conf.set("fs.azure.account.key.formula420.blob.core.windows.net", "s3f9bzNCqGGaSwqdpSFoofwcaxncyGe6dxcIFj9u2hrbxyyTx2nzG25kV3JYh+5QLERrIE0ZTDjZ+ASthbsy5w==")

# COMMAND ----------

raw_folder_path = "wasbs://raw@formula420.blob.core.windows.net"
processed_folder_path = "wasbs://processed@formula420.blob.core.windows.net"
presentation_folder_path = "wasbs://presentation@formula420.blob.core.windows.net"
