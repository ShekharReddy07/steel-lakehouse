
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Fails if any row has negative energy or negative tonnage
select *
from "steel"."main"."silver_plant"
where usage_kwh < 0
   or tonnes_produced < 0
  
  
      
    ) dbt_internal_test