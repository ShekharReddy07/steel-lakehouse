-- Fails if any row has negative energy or negative tonnage
select *
from {{ ref('silver_plant') }}
where usage_kwh < 0
   or tonnes_produced < 0
