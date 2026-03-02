import org.apache.spark.sql.*;
import static org.apache.spark.sql.functions.*;
import io.delta.tables.DeltaTable;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class SparkUtils {

    /**
     * Adds an ingestion_date column with the current timestamp.
     */
    public static Dataset<Row> addIngestionDate(Dataset<Row> inputDf) {
        return inputDf.withColumn("ingestion_date", current_timestamp());
    }

    /**
     * Re-arranges columns so the partition column is at the end.
     * Required for insertInto() operations.
     */
    public static Dataset<Row> reArrangePartitionColumn(Dataset<Row> inputDf, String partitionColumn) {
        List<Column> columns = new ArrayList<>();
        
        // Add all columns except the partition column
        for (String fieldName : inputDf.schema().fieldNames()) {
            if (!fieldName.equals(partitionColumn)) {
                columns.add(col(fieldName));
            }
        }
        // Add partition column at the end
        columns.add(col(partitionColumn));
        
        return inputDf.select(columns.toArray(new Column[0]));
    }

    /**
     * Overwrites a specific partition using dynamic partition overwrite mode.
     */
    public static void overwritePartition(SparkSession spark, Dataset<Row> inputDf, 
                                          String dbName, String tableName, String partitionColumn) {
        
        Dataset<Row> outputDf = reArrangePartitionColumn(inputDf, partitionColumn);
        spark.conf().set("spark.sql.sources.partitionOverwriteMode", "dynamic");
        
        String fullTableName = dbName + "." + tableName;
        
        if (spark.catalog().tableExists(fullTableName)) {
            outputDf.write().mode("overwrite").insertInto(fullTableName);
        } else {
            outputDf.write().mode("overwrite")
                    .partitionBy(partitionColumn)
                    .format("parquet")
                    .saveAsTable(fullTableName);
        }
    }

    /**
     * Collects unique values of a column into a Java List.
     */
    public static List<Object> dfColumnToList(Dataset<Row> inputDf, String columnName) {
        List<Row> rowList = inputDf.select(columnName).distinct().collectAsList();
        
        return rowList.stream()
                      .map(row -> row.get(0))
                      .collect(Collectors.toList());
    }

    /**
     * Merges data into a Delta table or creates it if it doesn't exist.
     */
    public static void mergeDeltaData(SparkSession spark, Dataset<Row> inputDf, 
                                     String dbName, String tableName, String folderPath, 
                                     String mergeCondition, String partitionColumn) {
        
        spark.conf().set("spark.databricks.optimizer.dynamicPartitionPruning", "true");
        String fullTableName = dbName + "." + tableName;

        if (spark.catalog().tableExists(fullTableName)) {
            // DeltaTable.forPath is the Java/Scala entry point for Delta operations
            DeltaTable deltaTable = DeltaTable.forPath(spark, folderPath + "/" + tableName);
            
            deltaTable.as("tgt")
                .merge(inputDf.as("src"), mergeCondition)
                .whenMatched().updateAll()
                .whenNotMatched().insertAll()
                .execute();
        } else {
            inputDf.write().mode("overwrite")
                    .partitionBy(partitionColumn)
                    .format("delta")
                    .saveAsTable(fullTableName);
        }
    }
}

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
