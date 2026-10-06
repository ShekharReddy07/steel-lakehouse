with raw as (
    select *
    from read_csv(
        '../data/raw/Steel_industry_data.csv',
        header = true,
        all_varchar = true,
        names = [
            'date', 'usage_kwh', 'lagging_reactive_kvarh', 'leading_reactive_kvarh',
            'co2_tco2', 'lagging_pf', 'leading_pf', 'nsm',
            'week_status', 'day_of_week', 'load_type'
        ]
    )
)

select
    strptime(date, '%d/%m/%Y %H:%M') as ts,
    cast(usage_kwh as double) as usage_kwh,
    cast(co2_tco2 as double) as co2_tco2,
    load_type
from raw
where date is not null
  and cast(usage_kwh as double) >= 0
qualify row_number() over (partition by date order by date) = 1
