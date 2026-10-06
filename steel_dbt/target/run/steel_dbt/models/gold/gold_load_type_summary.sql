
    

    create  table
      "steel"."main"."gold_load_type_summary__dbt_tmp"
  
    
    as (
      select
    load_type,
    count(*) as intervals,
    100.0 * count(*) / sum(count(*)) over () as pct_intervals,
    100.0 * sum(usage_kwh) / sum(sum(usage_kwh)) over () as pct_energy,
    sum(usage_kwh) / nullif(sum(tonnes_produced), 0) as kwh_per_tonne
from "steel"."main"."silver_plant"
group by load_type
    );
    
  