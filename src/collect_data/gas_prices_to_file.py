# gas_prices_to_file.py
import yfinance as yf
import json
import os
from datetime import datetime
from src.common_func.config import LANDING_ZONE, LOG_FILE_PATH

def collect_to_landing():
    try:
        # 1. Fetch
        ticker = yf.Ticker("TTF=F")
        df = ticker.history(period="1d")
        
        if df.empty:
            return
            
        # 2. Extract raw data
        latest = df.iloc[-1].to_dict()
        latest['timestamp'] = datetime.now().isoformat()
        latest['commodity'] = "TTF_GAS"
        
        # 3. Save to Landing Zone (JSONL format)
        filename = f"ttf_gas_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(LANDING_ZONE, filename)
        
        with open(filepath, 'a') as f:
            f.write(json.dumps(latest) + "\n")
            
    except Exception as e:
        with open(LOG_FILE_PATH, 'a') as log:
            log.write(f"{datetime.now()}: Collection Error - {str(e)}\n")

if __name__ == "__main__":
    collect_to_landing()