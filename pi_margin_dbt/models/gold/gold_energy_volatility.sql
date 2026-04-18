{{ config(materialized='view') }}

WITH base_metrics AS (
    SELECT 
        h.commodity_id,
        s.load_timestamp,
        s.close_price,
        -- Daily Returns for Volatility Calculation
        (s.close_price - LAG(s.close_price) OVER (PARTITION BY h.commodity_id ORDER BY s.load_timestamp)) 
            / NULLIF(LAG(s.close_price) OVER (PARTITION BY h.commodity_id ORDER BY s.load_timestamp), 0) AS daily_return
    FROM silver.main.hub_commodity h
    JOIN silver.main.sat_commodity_prices s ON h.hub_commodity_key = s.hub_commodity_key
),
volatility_logic AS (
    SELECT 
        *,
        -- 7-Day Volatility (Standard Deviation of Returns)
        STDDEV(daily_return) OVER (PARTITION BY commodity_id ORDER BY load_timestamp ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS vol_7d,
        -- 30-Day Baseline for Comparison
        AVG(close_price) OVER (PARTITION BY commodity_id ORDER BY load_timestamp ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d
    FROM base_metrics
)
SELECT 
    *,
    -- The "Signal" for the LLM
    CASE 
        WHEN vol_7d > (AVG(vol_7d) OVER () * 1.5) THEN 'HIGH'
        WHEN vol_7d < (AVG(vol_7d) OVER () * 0.5) THEN 'LOW'
        ELSE 'STABLE'
    END AS volatility_regime,
    (close_price / ma_30d) - 1 AS price_deviation_pct
FROM volatility_logic