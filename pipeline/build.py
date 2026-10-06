import sys
from pathlib import Path

import duckdb
import pandas as pd

from common import load_energy

energy = load_energy(sys.argv[1])
prod = pd.read_csv("data/raw/production.csv")

for layer in ["bronze", "silver", "gold"]:
    Path(f"data/{layer}").mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.register("raw_energy", energy)
con.register("raw_prod", prod)

# ---------- BRONZE ----------
con.execute("CREATE TABLE bronze_energy AS SELECT *, now() AS ingest_ts FROM raw_energy")
con.execute("CREATE TABLE bronze_production AS SELECT *, now() AS ingest_ts FROM raw_prod")

# ---------- SILVER ----------
con.execute("""
CREATE TABLE silver_energy AS
SELECT ts, usage_kwh, co2_tco2, load_type
FROM bronze_energy
WHERE ts IS NOT NULL AND usage_kwh >= 0
QUALIFY row_number() OVER (PARTITION BY ts ORDER BY ingest_ts) = 1
""")

con.execute("""
CREATE TABLE silver_production AS
SELECT
  CAST(ts AS TIMESTAMP) AS ts,
  tonnes_produced,
  CASE WHEN furnace_temp_c BETWEEN 800 AND 1800 THEN furnace_temp_c END AS furnace_temp_c,
  (furnace_temp_c IS NOT NULL AND furnace_temp_c NOT BETWEEN 800 AND 1800) AS is_sensor_anomaly,
  is_downtime,
  NULLIF(downtime_reason, '') AS downtime_reason,
  defect_count,
  NULLIF(defect_type, '') AS defect_type
FROM bronze_production
QUALIFY row_number() OVER (PARTITION BY CAST(ts AS TIMESTAMP) ORDER BY ingest_ts) = 1
""")

con.execute("""
CREATE TABLE silver_plant AS
SELECT
  e.ts, CAST(e.ts AS DATE) AS date, e.usage_kwh, e.co2_tco2, e.load_type,
  p.tonnes_produced, p.furnace_temp_c, p.is_sensor_anomaly,
  p.is_downtime, p.downtime_reason, p.defect_count, p.defect_type,
  CASE WHEN hour(e.ts) >= 6 AND hour(e.ts) < 14 THEN 'A'
       WHEN hour(e.ts) >= 14 AND hour(e.ts) < 22 THEN 'B'
       ELSE 'C' END AS shift
FROM silver_energy e
JOIN silver_production p ON e.ts = p.ts
""")

# ---------- DATA QUALITY CHECKS (each must be 0) ----------
checks = {
    "silver_energy duplicate ts": "SELECT COUNT(*) - COUNT(DISTINCT ts) FROM silver_energy",
    "silver_production duplicate ts": "SELECT COUNT(*) - COUNT(DISTINCT ts) FROM silver_production",
    "null timestamps": "SELECT COUNT(*) FROM silver_plant WHERE ts IS NULL",
    "negative energy": "SELECT COUNT(*) FROM silver_plant WHERE usage_kwh < 0",
    "negative tonnes": "SELECT COUNT(*) FROM silver_plant WHERE tonnes_produced < 0",
    "rows lost in join": "SELECT (SELECT COUNT(*) FROM silver_energy) - (SELECT COUNT(*) FROM silver_plant)",
}
print("\n== Data quality ==")
failed = False
for name, sql in checks.items():
    val = con.execute(sql).fetchone()[0]
    print(f"{'PASS' if val == 0 else 'FAIL'}  {name}: {val}")
    failed |= val != 0
if failed:
    raise SystemExit("Quality checks failed")

# ---------- GOLD ----------
con.execute("""
CREATE TABLE gold_daily_kpis AS
SELECT date,
  SUM(usage_kwh) AS total_kwh,
  SUM(tonnes_produced) AS total_tonnes,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne,
  SUM(co2_tco2) AS total_co2_t,
  SUM(CASE WHEN is_downtime THEN 15 ELSE 0 END) AS downtime_minutes,
  SUM(defect_count) AS defects,
  100.0 * SUM(defect_count) / NULLIF(SUM(tonnes_produced), 0) AS defects_per_100t,
  AVG(furnace_temp_c) AS avg_furnace_temp_c
FROM silver_plant GROUP BY date ORDER BY date
""")

con.execute("""
CREATE TABLE gold_load_type_summary AS
SELECT load_type,
  COUNT(*) AS intervals,
  100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS pct_intervals,
  100.0 * SUM(usage_kwh) / SUM(SUM(usage_kwh)) OVER () AS pct_energy,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne
FROM silver_plant GROUP BY load_type
""")

con.execute("""
CREATE TABLE gold_downtime_pareto AS
SELECT downtime_reason,
  COUNT(*) * 15 AS downtime_minutes,
  SUM(usage_kwh) AS idle_kwh_wasted
FROM silver_plant WHERE is_downtime
GROUP BY downtime_reason ORDER BY downtime_minutes DESC
""")

con.execute("""
CREATE TABLE gold_shift_summary AS
SELECT shift,
  SUM(usage_kwh) / NULLIF(SUM(tonnes_produced), 0) AS kwh_per_tonne,
  SUM(CASE WHEN is_downtime THEN 15 ELSE 0 END) AS downtime_minutes,
  100.0 * SUM(defect_count) / NULLIF(SUM(tonnes_produced), 0) AS defects_per_100t
FROM silver_plant GROUP BY shift ORDER BY shift
""")

# ---------- EXPORT ----------
for t in ["bronze_energy", "bronze_production"]:
    con.execute(f"COPY (SELECT * FROM {t}) TO 'data/bronze/{t}.parquet' (FORMAT PARQUET)")
for t in ["silver_energy", "silver_production", "silver_plant"]:
    con.execute(f"COPY (SELECT * FROM {t}) TO 'data/silver/{t}.parquet' (FORMAT PARQUET)")
for t in ["gold_daily_kpis", "gold_load_type_summary", "gold_downtime_pareto", "gold_shift_summary"]:
    con.execute(f"COPY (SELECT * FROM {t}) TO 'data/gold/{t}.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT * FROM {t}) TO 'data/gold/{t}.csv' (HEADER, DELIMITER ',')")

print("\n== Gold: load type summary ==")
print(con.execute("SELECT * FROM gold_load_type_summary").df())
print("\n== Gold: downtime pareto ==")
print(con.execute("SELECT * FROM gold_downtime_pareto").df())
print("\nDone. Outputs in data/bronze, data/silver, data/gold")