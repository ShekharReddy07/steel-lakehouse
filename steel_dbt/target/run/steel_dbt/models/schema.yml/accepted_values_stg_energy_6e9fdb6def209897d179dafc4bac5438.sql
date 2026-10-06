
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        load_type as value_field,
        count(*) as n_records

    from "steel"."main"."stg_energy"
    group by load_type

)

select *
from all_values
where value_field not in (
    'Light_Load','Medium_Load','Maximum_Load'
)



  
  
      
    ) dbt_internal_test