
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select usage_kwh
from "steel"."main"."stg_energy"
where usage_kwh is null



  
  
      
    ) dbt_internal_test