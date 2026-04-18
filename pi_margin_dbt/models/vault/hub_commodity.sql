{{ config(
    materialized='external',
    location='/home/kaushik/pi-margin/data/silver/hub_commodity.parquet'
) }}

SELECT 
    hub_commodity_key,
    symbol AS commodity_id,
    MIN(load_timestamp) AS load_timestamp,
    record_source
FROM {{ ref('stg_gas_prices') }}
GROUP BY 
    hub_commodity_key, 
    symbol, 
    record_source