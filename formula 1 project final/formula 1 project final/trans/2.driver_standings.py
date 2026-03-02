import org.apache.spark.sql.*;
import org.apache.spark.sql.expressions.Window;
import org.apache.spark.sql.expressions.WindowSpec;
import static org.apache.spark.sql.functions.*;
import java.util.List;

public class TransformDriverStandings {
    public static void main(String[] args) {

        SparkSession spark = SparkSession.builder()
                .appName("TransformDriverStandings")
                .getOrCreate();

        // Parameters
        String vFileDate = spark.conf().get("p_file_date", "2021-03-28");
        String presentationPath = "wasbs://presentation@formula420.blob.core.windows.net";

        // ##### Step 1 - Find race years to reprocess
        Dataset<Row> raceResultsDf = spark.read().format("delta").load(presentationPath + "/race_results");
        
        // Filter by file date and extract distinct years to a Java List
        List<Integer> raceYearList = raceResultsDf
                .filter(col("file_date").equalTo(vFileDate))
                .select("race_year")
                .distinct()
                .as(Encoders.INT())
                .collectAsList();

        // ##### Step 2 - Filter data for those specific years
        // In Java, we convert the List to an array for the isin function
        Dataset<Row> filteredResultsDf = raceResultsDf
                .filter(col("race_year").isin(raceYearList.toArray()));

        // ##### Step 3 - Aggregate Standing Data
        Dataset<Row> driverStandingsDf = filteredResultsDf
                .groupBy("race_year", "driver_name", "driver_nationality")
                .agg(
                    sum("points").alias("total_points"),
                    count(when(col("position").equalTo(1), true)).alias("wins")
                );

        // ##### Step 4 - Apply Window Function for Ranking
        // Partition by year, order by points (desc) then wins (desc)
        WindowSpec driverRankSpec = Window.partitionBy("race_year")
                .orderBy(desc("total_points"), desc("wins"));

        Dataset<Row> finalDf = driverStandingsDf
                .withColumn("rank", rank().over(driverRankSpec));

        // ##### Step 5 - Delta Merge
        String mergeCondition = "tgt.driver_name = src.driver_name AND tgt.race_year = src.race_year";

        SparkUtils.mergeDeltaData(
            spark, 
            finalDf, 
            "f1_presentation", 
            "driver_standings", 
            presentationPath, 
            mergeCondition, 
            "race_year"
        );

        System.out.println("Driver Standings Transformation Successful.");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ##### Produce driver standings

# COMMAND ----------

dbutils.widgets.text("p_file_date", "2021-03-28")
v_file_date = dbutils.widgets.get("p_file_date")

# COMMAND ----------

# MAGIC %run "../includes/common_functions"

# COMMAND ----------

# MAGIC %run "../includes/configuration"

# COMMAND ----------

# MAGIC %md
# MAGIC Find race years for which the data is to be reprocessed

# COMMAND ----------

race_results_df = spark.read.format("delta").load(f"{presentation_folder_path}/race_results") \
.filter(f"file_date = '{v_file_date}'") 

# COMMAND ----------

race_year_list = df_column_to_list(race_results_df, 'race_year')

# COMMAND ----------

from pyspark.sql.functions import col

race_results_df = spark.read.format("delta").load(f"{presentation_folder_path}/race_results") \
.filter(col("race_year").isin(race_year_list))

# COMMAND ----------

from pyspark.sql.functions import sum, when, count, col

driver_standings_df = race_results_df \
.groupBy("race_year", "driver_name", "driver_nationality") \
.agg(sum("points").alias("total_points"),
     count(when(col("position") == 1, True)).alias("wins"))

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import desc, rank, asc

driver_rank_spec = Window.partitionBy("race_year").orderBy(desc("total_points"), desc("wins"))
final_df = driver_standings_df.withColumn("rank", rank().over(driver_rank_spec))

# COMMAND ----------

merge_condition = "tgt.driver_name = src.driver_name AND tgt.race_year = src.race_year"
merge_delta_data(final_df, 'f1_presentation', 'driver_standings', presentation_folder_path, merge_condition, 'race_year')

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_presentation.driver_standings WHERE race_year = 2021;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT race_year, COUNT(1)
# MAGIC   FROM f1_presentation.driver_standings
# MAGIC  GROUP BY race_year
# MAGIC  ORDER BY race_year DESC;

# COMMAND ----------

