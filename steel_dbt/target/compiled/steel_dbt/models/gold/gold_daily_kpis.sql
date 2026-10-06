select
    date,
    sum(usage_kwh) as total_kwh,
    sum(tonnes_produced) as total_tonnes,
    sum(usage_kwh) / nullif(sum(tonnes_produced), 0) as kwh_per_tonne,
    sum(co2_tco2) as total_co2_t,
    sum(case when is_downtime then 15 else 0 end) as downtime_minutes,
    sum(defect_count) as defects,
    100.0 * sum(defect_count) / nullif(sum(tonnes_produced), 0) as defects_per_100t,
    avg(furnace_temp_c) as avg_furnace_temp_c
from "steel"."main"."silver_plant"
group by date
order by date