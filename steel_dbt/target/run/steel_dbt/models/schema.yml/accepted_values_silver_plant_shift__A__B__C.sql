
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        shift as value_field,
        count(*) as n_records

    from "steel"."main"."silver_plant"
    group by shift

)

select *
from all_values
where value_field not in (
    'A','B','C'
)



  
  
      
    ) dbt_internal_test