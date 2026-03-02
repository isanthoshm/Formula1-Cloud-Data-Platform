import org.apache.spark.sql.*;
import org.apache.spark.sql.expressions.Window;
import org.apache.spark.sql.expressions.WindowSpec;
import static org.apache.spark.sql.functions.*;
import java.util.List;

public class TransformConstructorStandings {
    public static void main(String[] args) {

        SparkSession spark = SparkSession.builder()
                .appName("TransformConstructorStandings")
                .getOrCreate();

        // Parameters
        String vFileDate = spark.conf().get("p_file_date", "2021-03-28");
        String presentationPath = "wasbs://presentation@formula420.blob.core.windows.net";

        // ##### Step 1 - Find race years to reprocess
        Dataset<Row> raceResultsDf = spark.read().format("delta").load(presentationPath + "/race_results");
        
        // Extract distinct years affected by the current file_date
        List<Integer> raceYearList = raceResultsDf
                .filter(col("file_date").equalTo(vFileDate))
                .select("race_year")
                .distinct()
                .as(Encoders.INT())
                .collectAsList();

        // ##### Step 2 - Filter data for those specific years
        // We convert the Java List to an array for the isin function
        Dataset<Row> filteredResultsDf = raceResultsDf
                .filter(col("race_year").isin(raceYearList.toArray()));

        // ##### Step 3 - Aggregate Team Performance
        Dataset<Row> constructorStandingsDf = filteredResultsDf
                .groupBy("race_year", "team")
                .agg(
                    sum("points").alias("total_points"),
                    count(when(col("position").equalTo(1), true)).alias("wins")
                );

        // ##### Step 4 - Rank Constructors within each Season
        // Order by total_points DESC, then wins DESC to break ties
        WindowSpec constructorRankSpec = Window.partitionBy("race_year")
                .orderBy(desc("total_points"), desc("wins"));

        Dataset<Row> finalDf = constructorStandingsDf
                .withColumn("rank", rank().over(constructorRankSpec));

        // ##### Step 5 - Delta Merge to Presentation Layer
        String mergeCondition = "tgt.team = src.team AND tgt.race_year = src.race_year";

        SparkUtils.mergeDeltaData(
            spark, 
            finalDf, 
            "f1_presentation", 
            "constructor_standings", 
            presentationPath, 
            mergeCondition, 
            "race_year"
        );

        System.out.println("Constructor Standings Transformation Completed Successfully.");
        spark.stop();
    }
}

# Databricks notebook source
# MAGIC %md
# MAGIC ##### Produce constructor standings

# COMMAND ----------

dbutils.widgets.text("p_file_date", "2021-03-28")
v_file_date = dbutils.widgets.get("p_file_date")

# COMMAND ----------

# MAGIC %run "../includes/configuration"

# COMMAND ----------

# MAGIC %run "../includes/common_functions"

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

constructor_standings_df = race_results_df \
.groupBy("race_year", "team") \
.agg(sum("points").alias("total_points"),
     count(when(col("position") == 1, True)).alias("wins"))

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import desc, rank, asc

constructor_rank_spec = Window.partitionBy("race_year").orderBy(desc("total_points"), desc("wins"))
final_df = constructor_standings_df.withColumn("rank", rank().over(constructor_rank_spec))

# COMMAND ----------

merge_condition = "tgt.team = src.team AND tgt.race_year = src.race_year"
merge_delta_data(final_df, 'f1_presentation', 'constructor_standings', presentation_folder_path, merge_condition, 'race_year')

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM f1_presentation.constructor_standings WHERE race_year = 2021;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT race_year, COUNT(1)
# MAGIC   FROM f1_presentation.constructor_standings
# MAGIC  GROUP BY race_year
# MAGIC  ORDER BY race_year DESC;
