
    
    

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


