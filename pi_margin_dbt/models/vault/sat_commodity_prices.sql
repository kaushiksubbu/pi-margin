{{ config(materialized='external', location='/home/kaushik/pi-margin/data/silver/sat_commodity_prices.parquet') }}

SELECT
    hub_commodity_key,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    hash_diff,
    load_timestamp,
    record_source
FROM {{ ref('stg_gas_prices') }}