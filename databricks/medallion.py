# Databricks notebook source
# MAGIC %md
# MAGIC # Steel plant medallion pipeline (Delta)
# MAGIC Reads bronze Parquet from a Unity Catalog Volume, builds silver and gold Delta tables.

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "workspace"
SCHEMA = "steel"
T = f"{CATALOG}.{SCHEMA}"
VOL = f"/Volumes/{CATALOG}/{SCHEMA}/raw_files"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {T}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {T}.raw_files")
print("Upload bronze_energy.parquet and bronze_production.parquet to", VOL)

# COMMAND ----------

# BRONZE: raw data as Delta tables
be = spark.read.parquet(f"{VOL}/bronze_energy.parquet")
bp = spark.read.parquet(f"{VOL}/bronze_production.parquet")
be.write.mode("overwrite").saveAsTable(f"{T}.bronze_energy")
bp.write.mode("overwrite").saveAsTable(f"{T}.bronze_production")
print("bronze rows:", be.count(), bp.count())

# COMMAND ----------

# SILVER: dedupe, clean, flag sensor anomalies, join, derive shift
silver_energy = (
    spark.table(f"{T}.bronze_energy")
    .where(F.col("ts").isNotNull() & (F.col("usage_kwh") >= 0))
    .dropDuplicates(["ts"])
    .select("ts", "usage_kwh", "co2_tco2", "load_type")
)

silver_prod = (
    spark.table(f"{T}.bronze_production")
    .withColumn("ts", F.col("ts").cast("timestamp"))
    .dropDuplicates(["ts"])
    .withColumn(
        "is_sensor_anomaly",
        F.col("furnace_temp_c").isNotNull() & ~F.col("furnace_temp_c").between(800, 1800),
    )
    .withColumn(
        "furnace_temp_c",
        F.when(F.col("furnace_temp_c").between(800, 1800), F.col("furnace_temp_c")),
    )
    .withColumn("is_downtime", F.col("is_downtime").cast("boolean"))
    .select("ts", "tonnes_produced", "furnace_temp_c", "is_sensor_anomaly",
            "is_downtime", "downtime_reason", "defect_count", "defect_type")
)

silver_plant = (
    silver_energy.join(silver_prod, "ts")
    .withColumn("date", F.to_date("ts"))
    .withColumn(
        "shift",
        F.when((F.hour("ts") >= 6) & (F.hour("ts") < 14), "A")
         .when((F.hour("ts") >= 14) & (F.hour("ts") < 22), "B")
         .otherwise("C"),
    )
)

silver_plant.write.mode("overwrite").saveAsTable(f"{T}.silver_plant")
print("silver_plant rows:", silver_plant.count())

# COMMAND ----------

# GOLD marts
spark.sql(f"""
CREATE OR REPLACE TABLE {T}.gold_daily_kpis AS
SELECT date,
  SUM(usage_kwh) AS total_kwh,
  SUM(tonnes_produced) AS total_tonnes,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne,
  SUM(co2_tco2) AS total_co2_t,
  SUM(CASE WHEN is_downtime THEN 15 ELSE 0 END) AS downtime_minutes,
  SUM(defect_count) AS defects
FROM {T}.silver_plant GROUP BY date
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {T}.gold_load_type_summary AS
SELECT load_type,
  COUNT(*) AS intervals,
  100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS pct_intervals,
  100.0 * SUM(usage_kwh) / SUM(SUM(usage_kwh)) OVER () AS pct_energy,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne
FROM {T}.silver_plant GROUP BY load_type
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {T}.gold_downtime_pareto AS
SELECT downtime_reason,
  COUNT(*) * 15 AS downtime_minutes,
  SUM(usage_kwh) AS idle_kwh_wasted
FROM {T}.silver_plant WHERE is_downtime
GROUP BY downtime_reason
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {T}.gold_shift_summary AS
SELECT shift,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne,
  SUM(CASE WHEN is_downtime THEN 15 ELSE 0 END) AS downtime_minutes
FROM {T}.silver_plant GROUP BY shift
""")

# COMMAND ----------

# Verify: should match the dashboard (about 47.63 kWh per tonne)
display(spark.sql(f"""
SELECT ROUND(SUM(usage_kwh)) AS total_kwh,
       ROUND(SUM(tonnes_produced)) AS total_tonnes,
       ROUND(SUM(usage_kwh) / SUM(tonnes_produced), 2) AS kwh_per_tonne
FROM {T}.silver_plant
"""))
display(spark.table(f"{T}.gold_load_type_summary"))