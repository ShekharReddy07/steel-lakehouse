
    

    create  table
      "steel"."main"."gold_shift_summary__dbt_tmp"
  
    
    as (
      select
    shift,
    sum(usage_kwh) / nullif(sum(tonnes_produced), 0) as kwh_per_tonne,
    sum(case when is_downtime then 15 else 0 end) as downtime_minutes,
    100.0 * sum(defect_count) / nullif(sum(tonnes_produced), 0) as defects_per_100t
from "steel"."main"."silver_plant"
group by shift
order by shift
    );
    
  