
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select tonnes_produced
from "steel"."main"."stg_production"
where tonnes_produced is null



  
  
      
    ) dbt_internal_test