{{ config(materialized='view') }}

SELECT
    -- 1. The Hub Key (Hash of the symbol/ID)
    md5(upper(trim(symbol))) AS hub_commodity_key,

    -- 2. The Hash Diff (Fingerprint of the prices)
    md5(
        coalesce(cast(open_price as varchar), '') || 
        coalesce(cast(high_price as varchar), '') || 
        coalesce(cast(low_price as varchar), '') || 
        coalesce(cast(close_price as varchar), '')
    ) AS hash_diff,

    -- 3. The data
    symbol,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    "date" AS load_timestamp,
    'YAHOO_FINANCE' AS record_source
FROM bronze.main.gas_prices_raw