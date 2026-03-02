import org.apache.spark.sql.*;
import static org.apache.spark.sql.functions.*;
import io.delta.tables.*;

public class TransformCalculatedRaceResults {
    public static void main(String[] args) {

        SparkSession spark = SparkSession.builder()
                .appName("TransformCalculatedRaceResults")
                .getOrCreate();

        // Parameters
        String vFileDate = spark.conf().get("p_file_date", "2021-03-21");

        // ##### Step 1 - Create the Target Delta Table if it doesn't exist
        spark.sql("CREATE TABLE IF NOT EXISTS f1_presentation.calculated_race_results (" +
                "race_year INT, team_name STRING, driver_id INT, driver_name STRING, " +
                "race_id INT, position INT, points INT, calculated_points INT, " +
                "created_date TIMESTAMP, updated_date TIMESTAMP) USING DELTA");

        // ##### Step 2 - Prepare Source Data (Calculated Results)
        // We calculate points as: 11 - position
        Dataset<Row> updatesDf = spark.read().table("f1_processed.results")
                .filter(col("file_date").equalTo(vFileDate).and(col("position").leq(10)))
                .join(spark.read().table("f1_processed.drivers"), "driver_id")
                .join(spark.read().table("f1_processed.constructors"), "constructor_id")
                .join(spark.read().table("f1_processed.races"), "race_id")
                .select(
                    col("races.race_year"),
                    col("constructors.name").as("team_name"),
                    col("drivers.driver_id"),
                    col("drivers.name").as("driver_name"),
                    col("races.race_id"),
                    col("results.position"),
                    col("results.points"),
                    expr("11 - results.position").as("calculated_points")
                );

        // ##### Step 3 - Perform Delta Merge
        DeltaTable targetTable = DeltaTable.forName(spark, "f1_presentation.calculated_race_results");

        targetTable.as("tgt")
            .merge(updatesDf.as("upd"), "tgt.driver_id = upd.driver_id AND tgt.race_id = upd.race_id")
            .whenMatched()
                .updateExpr(new java.util.HashMap<String, String>() {{
                    put("position", "upd.position");
                    put("points", "upd.points");
                    put("calculated_points", "upd.calculated_points");
                    put("updated_date", "current_timestamp()");
                }})
            .whenNotMatched()
                .insertExpr(new java.util.HashMap<String, String>() {{
                    put("race_year", "upd.race_year");
                    put("team_name", "upd.team_name");
                    put("driver_id", "upd.driver_id");
                    put("driver_name", "upd.driver_name");
                    put("race_id", "upd.race_id");
                    put("position", "upd.position");
                    put("points", "upd.points");
                    put("calculated_points", "upd.calculated_points");
                    put("created_date", "current_timestamp()");
                }})
            .execute();

        System.out.println("Calculated Race Results Merge Successful.");
        spark.stop();
    }
}

# Databricks notebook source
dbutils.widgets.text("p_file_date", "2021-03-21")
v_file_date = dbutils.widgets.get("p_file_date")

# COMMAND ----------

spark.sql(f"""
              CREATE TABLE IF NOT EXISTS f1_presentation.calculated_race_results
              (
              race_year INT,
              team_name STRING,
              driver_id INT,
              driver_name STRING,
              race_id INT,
              position INT,
              points INT,
              calculated_points INT,
              created_date TIMESTAMP,
              updated_date TIMESTAMP
              )
              USING DELTA
""")

# COMMAND ----------

spark.sql(f"""
              CREATE OR REPLACE TEMP VIEW race_result_updated
              AS
              SELECT races.race_year,
                     constructors.name AS team_name,
                     drivers.driver_id,
                     drivers.name AS driver_name,
                     races.race_id,
                     results.position,
                     results.points,
                     11 - results.position AS calculated_points
                FROM f1_processed.results 
                JOIN f1_processed.drivers ON (results.driver_id = drivers.driver_id)
                JOIN f1_processed.constructors ON (results.constructor_id = constructors.constructor_id)
                JOIN f1_processed.races ON (results.race_id = races.race_id)
               WHERE results.position <= 10
                 AND results.file_date = '{v_file_date}'
""")

# COMMAND ----------

spark.sql(f"""
              MERGE INTO f1_presentation.calculated_race_results tgt
              USING race_result_updated upd
              ON (tgt.driver_id = upd.driver_id AND tgt.race_id = upd.race_id)
              WHEN MATCHED THEN
                UPDATE SET tgt.position = upd.position,
                           tgt.points = upd.points,
                           tgt.calculated_points = upd.calculated_points,
                           tgt.updated_date = current_timestamp
              WHEN NOT MATCHED
                THEN INSERT (race_year, team_name, driver_id, driver_name,race_id, position, points, calculated_points, created_date ) 
                     VALUES (race_year, team_name, driver_id, driver_name,race_id, position, points, calculated_points, current_timestamp)
       """)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(1) FROM race_result_updated;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(1) FROM f1_presentation.calculated_race_results;

# COMMAND ----------

