
    

    create  table
      "steel"."main"."silver_plant__dbt_tmp"
  
    
    as (
      select
    e.ts,
    cast(e.ts as date) as date,
    e.usage_kwh,
    e.co2_tco2,
    e.load_type,
    p.tonnes_produced,
    p.furnace_temp_c,
    p.is_sensor_anomaly,
    p.is_downtime,
    p.downtime_reason,
    p.defect_count,
    p.defect_type,
    case
        when hour(e.ts) >= 6 and hour(e.ts) < 14 then 'A'
        when hour(e.ts) >= 14 and hour(e.ts) < 22 then 'B'
        else 'C'
    end as shift
from "steel"."main"."stg_energy" e
join "steel"."main"."stg_production" p on e.ts = p.ts
    );
    
  