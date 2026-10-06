
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ts
from "steel"."main"."stg_production"
where ts is null



  
  
      
    ) dbt_internal_test