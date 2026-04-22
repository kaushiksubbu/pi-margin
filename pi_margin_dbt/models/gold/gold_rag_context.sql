{{ config(
    materialized='table',
    alias='gold_rag_context'
) }}

SELECT 
    commodity_id,
    'KNOWLEDGE_BASE_ENTRY: ' || 
    'Commodity: ' || commodity_id || '. ' ||
    'As of ' || load_timestamp || ', the market price is ' || close_price || '. ' ||
    -- NEW LOGIC START --
    'Trend: ' || 
    CASE 
        WHEN price_deviation_pct > 0.5 THEN 'BULLISH (Upward Momentum)'
        WHEN price_deviation_pct < -0.5 THEN 'BEARISH (Downward Pressure)'
        ELSE 'NEUTRAL (Range Bound)'
    END || '. ' ||
    -- NEW LOGIC END --
    'Analysis: The market is currently in a ' || volatility_regime || ' state. ' || 
    'Impact: Predicted margin erosion is ' || price_deviation_pct || '%. ' ||      
    'Recommendation: ' || 
    CASE 
        WHEN volatility_regime = 'HIGH' THEN 'Trigger immediate price review.'
        ELSE 'Maintain strategy.'
    END as chunk_text
FROM {{ ref('gold_energy_volatility') }}