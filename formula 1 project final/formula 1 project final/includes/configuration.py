# Databricks notebook source
spark.conf.set("fs.azure.account.key.formula420.blob.core.windows.net", "s3f9bzNCqGGaSwqdpSFoofwcaxncyGe6dxcIFj9u2hrbxyyTx2nzG25kV3JYh+5QLERrIE0ZTDjZ+ASthbsy5w==")

# COMMAND ----------

raw_folder_path = "wasbs://raw@formula420.blob.core.windows.net"
processed_folder_path = "wasbs://processed@formula420.blob.core.windows.net"
presentation_folder_path = "wasbs://presentation@formula420.blob.core.windows.net"