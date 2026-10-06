with raw as (
    select * from read_csv_auto('../data/raw/production.csv')
)

select
    cast(ts as timestamp) as ts,
    tonnes_produced,
    case when furnace_temp_c between 800 and 1800 then furnace_temp_c end as furnace_temp_c,
    (furnace_temp_c is not null and furnace_temp_c not between 800 and 1800) as is_sensor_anomaly,
    cast(is_downtime as boolean) as is_downtime,
    nullif(cast(downtime_reason as varchar), '') as downtime_reason,
    defect_count,
    nullif(cast(defect_type as varchar), '') as defect_type
from raw
qualify row_number() over (partition by cast(ts as timestamp) order by ts) = 1