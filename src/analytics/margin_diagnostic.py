import duckdb
import pandas as pd

def run_margin_simulation(commodity_symbol, baseline_margin):
    # Connect to the primary analytics database
    con = duckdb.connect('/home/kaushik/pi-margin/data/databases/analytics.db')
    
    # --- ADD THESE LINES TO BRIDGE THE DATABASES ---
    con.execute("ATTACH IF NOT EXISTS '/home/kaushik/pi-margin/data/databases/raw_source.db' AS bronze")
    con.execute("ATTACH IF NOT EXISTS '/home/kaushik/pi-margin/data/databases/master_data.db' AS silver")
    # -----------------------------------------------
    
    # 1. Retrieve the latest 'Facts' from Gold
    latest_stats = con.execute(f"""
        SELECT close_price, vol_7d, volatility_regime 
        FROM gold_energy_volatility 
        WHERE commodity_id = '{commodity_symbol}'
        ORDER BY load_timestamp DESC LIMIT 1
    """).fetchone()
    
    # 2. Retrieve the 'Sensitivity' for the business
    sensitivity = con.execute(f"""
        SELECT category_name, sensitivity_factor 
        FROM silver.margin_sensitivity 
        WHERE commodity_id = '{commodity_symbol}'
    """).df()
    
    # 3. The "What-If" Logic
    results = []
    for _, row in sensitivity.iterrows():
        impact = baseline_margin * row['sensitivity_factor']
        results.append({
            "Category": row['category_name'],
            "Scenario": f"{baseline_margin}% Hike",
            "Predicted_Margin_Erosion": f"{impact:.2f}%",
            "Current_Market_State": latest_stats[2]
        })
    
    return pd.DataFrame(results)

# Example Simulation: 15% Gas Spike
print(run_margin_simulation('TTF_GAS', 15.0))