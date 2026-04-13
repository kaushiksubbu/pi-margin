# src/collect_data/gas_prices.py
import yfinance as yf
import json
import os
from datetime import datetime
from src.common_func.config import TTF_GAS_TICKER, LOG_DIR

def log_event(event_type: str, status: str, metadata: dict):
    """Appends execution logs to a JSONL file."""
    log_path = os.path.join(LOG_DIR, "collection_audit.jsonl")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "status": status,
        **metadata
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def fetch_ttf_gas_prices():
    """Fetches Dutch TTF Gas futures and logs results silently."""
    try:
        ticker = yf.Ticker(TTF_GAS_TICKER)
        df = ticker.history(period="1d")
        
        if df.empty:
            log_event("gas_price_fetch", "EMPTY", {"ticker": TTF_GAS_TICKER})
            return None
            
        latest = df.iloc[-1]
        data = {
            "timestamp": datetime.now().isoformat(),
            "commodity": "TTF_GAS",
            "price_close": float(latest['Close']),
            "volume": int(latest['Volume']),
            "currency": "EUR"
        }
        
        log_event("gas_price_fetch", "SUCCESS", {"rows": 1, "ticker": TTF_GAS_TICKER})
        return [data]

    except Exception as e:
        log_event("gas_price_fetch", "ERROR", {"error": str(e)})
        return None

if __name__ == "__main__":
    fetch_ttf_gas_prices()