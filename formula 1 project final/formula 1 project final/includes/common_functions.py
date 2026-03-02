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

# Databricks notebook source
from pyspark.sql.functions import current_timestamp
def add_ingestion_date(input_df):
  output_df = input_df.withColumn("ingestion_date", current_timestamp())
  return output_df

# COMMAND ----------

def re_arrange_partition_column(input_df, partition_column):
  column_list = []
  for column_name in input_df.schema.names:
    if column_name != partition_column:
      column_list.append(column_name)
  column_list.append(partition_column)
  output_df = input_df.select(column_list)
  return output_df

# COMMAND ----------

def overwrite_partition(input_df, db_name, table_name, partition_column):
  output_df = re_arrange_partition_column(input_df, partition_column)
  spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")
  if (spark._jsparkSession.catalog().tableExists(f"{db_name}.{table_name}")):
    output_df.write.mode("overwrite").insertInto(f"{db_name}.{table_name}")
  else:
    output_df.write.mode("overwrite").partitionBy(partition_column).format("parquet").saveAsTable(f"{db_name}.{table_name}")

# COMMAND ----------

def df_column_to_list(input_df, column_name):
  df_row_list = input_df.select(column_name) \
                        .distinct() \
                        .collect()
  
  column_value_list = [row[column_name] for row in df_row_list]
  return column_value_list

# COMMAND ----------

def merge_delta_data(input_df, db_name, table_name, folder_path, merge_condition, partition_column):
  spark.conf.set("spark.databricks.optimizer.dynamicPartitionPruning","true")

  from delta.tables import DeltaTable
  if (spark._jsparkSession.catalog().tableExists(f"{db_name}.{table_name}")):
    deltaTable = DeltaTable.forPath(spark, f"{folder_path}/{table_name}")
    deltaTable.alias("tgt").merge(
        input_df.alias("src"),
        merge_condition) \
      .whenMatchedUpdateAll()\
      .whenNotMatchedInsertAll()\
      .execute()
  else:
    input_df.write.mode("overwrite").partitionBy(partition_column).format("delta").saveAsTable(f"{db_name}.{table_name}")

# COMMAND ----------

