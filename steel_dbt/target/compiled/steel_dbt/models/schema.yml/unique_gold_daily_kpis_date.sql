
    
    

select
    date as unique_field,
    count(*) as n_records

from "steel"."main"."gold_daily_kpis"
where date is not null
group by date
having count(*) > 1


