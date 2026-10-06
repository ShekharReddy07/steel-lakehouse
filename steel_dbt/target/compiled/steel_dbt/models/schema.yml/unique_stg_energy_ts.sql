
    
    

select
    ts as unique_field,
    count(*) as n_records

from "steel"."main"."stg_energy"
where ts is not null
group by ts
having count(*) > 1


