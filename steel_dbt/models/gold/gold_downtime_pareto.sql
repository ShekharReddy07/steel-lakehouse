select
    downtime_reason,
    count(*) * 15 as downtime_minutes,
    sum(usage_kwh) as idle_kwh_wasted
from {{ ref('silver_plant') }}
where is_downtime
group by downtime_reason
order by downtime_minutes desc
