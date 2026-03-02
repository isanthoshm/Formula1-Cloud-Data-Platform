import org.apache.spark.sql.SparkSession;
import java.util.HashMap;
import java.util.Map;

public class IngestionManager {
    public static void main(String[] args) {
        
        // 1. Initialize the shared Spark Session
        SparkSession spark = SparkConfig.getSparkSession();

        // 2. Set up parameters (similar to dbutils widgets)
        String dataSource = "Ergast API";
        String fileDate = "2021-04-18";

        // Inject parameters into Spark Config so child classes can access them
        spark.conf().set("p_data_source", dataSource);
        spark.conf().set("p_file_date", fileDate);

        try {
            System.out.println("Starting Full Ingestion Pipeline...");

            // 3. Sequential Execution (Equivalent to your notebook cells)
            runIngestion("Circuits", () -> IngestCircuits.main(new String[]{}));
            runIngestion("Races", () -> IngestRaces.main(new String[]{}));
            runIngestion("Constructors", () -> IngestConstructors.main(new String[]{}));
            runIngestion("Drivers", () -> IngestDrivers.main(new String[]{}));
            runIngestion("Results", () -> IngestResults.main(new String[]{}));
            runIngestion("Pit Stops", () -> IngestPitStops.main(new String[]{}));
            runIngestion("Lap Times", () -> IngestLapTimes.main(new String[]{}));
            runIngestion("Qualifying", () -> IngestQualifying.main(new String[]{}));

            System.out.println("All Ingestions Completed Successfully.");

        } catch (Exception e) {
            System.err.println("Pipeline failed: " + e.getMessage());
            System.exit(1);
        } finally {
            spark.stop();
        }
    }

    /**
     * Helper method to wrap execution with logging (Equivalent to v_result logging)
     */
    private static void runIngestion(String name, Runnable ingestionTask) {
        System.out.println(">>> Running Ingestion: " + name);
        ingestionTask.run();
        System.out.println(">>> Finished Ingestion: " + name + " [Success]");
    }
}
# Databricks notebook source
v_result = dbutils.notebook.run("1.ingest_circuits_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("2.ingest_races_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("3.ingest_constructors_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("4.ingest_drivers_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("5.ingest_results_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("6.ingest_pit_stops_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("7.ingest_lap_times_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

v_result = dbutils.notebook.run("8.ingest_qualifying_file", 0, {"p_data_source": "Ergast API", "p_file_date": "2021-04-18"})

# COMMAND ----------

v_result

# COMMAND ----------

