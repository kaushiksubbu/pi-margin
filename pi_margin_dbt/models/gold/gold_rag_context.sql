{{ config(materialized='view') }}

SELECT 
    commodity_id,
    'KNOWLEDGE_BASE_ENTRY: ' || 
    'Commodity: ' || commodity_id || '. ' ||
    'As of ' || load_timestamp || ', the market price is ' || close_price || '. ' ||
    'Analysis: The market is currently in a ' || volatility_regime || ' state. ' || 
    'Impact: Predicted margin erosion is ' || price_deviation_pct || '%. ' ||      
    'Recommendation: ' || 
    CASE 
        WHEN volatility_regime = 'HIGH' THEN 'Trigger immediate price review.'
        ELSE 'Maintain strategy.'
    END as chunk_text
FROM {{ ref('gold_energy_volatility') }}