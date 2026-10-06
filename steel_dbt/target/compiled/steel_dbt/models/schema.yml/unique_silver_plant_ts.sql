
    
    

select
    ts as unique_field,
    count(*) as n_records

from "steel"."main"."silver_plant"
where ts is not null
group by ts
having count(*) > 1


