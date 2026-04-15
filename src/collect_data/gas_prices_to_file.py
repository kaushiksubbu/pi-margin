# gas_prices_to_file.py
import yfinance as yf
import json
import os
from datetime import datetime
from src.common_func.config import LANDING_ZONE, LOG_DIR
import logging

# Configure standard logging to JSONL
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'collection_audit.jsonl'),
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
)

def log_to_jsonl(level, module, message_dict):
    """Structured logging for file-based debugging."""
    log_msg = json.dumps(message_dict)
    if level == "INFO":
        logging.info(log_msg)
    elif level == "ERROR":
        logging.error(log_msg)


def collect_to_landing():
    try:
        # 1. Fetch
        ticker = yf.Ticker("TTF=F")
        df = ticker.history(period="1d")
        
        if df.empty:
            log_to_jsonl("INFO", "fetch", {"source": "TTF_GAS", "message": "API returned empty dataframe"})
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
            log_to_jsonl("INFO", "ingestion", {"source": "TTF_GAS", "status": "success", "rows": sum(1 for _ in open(filepath))})
    except Exception as e:
        log_to_jsonl("ERROR", "fetch", {"source": "TTF_GAS", "status": "fail", "error": str(e)})

if __name__ == "__main__":
    collect_to_landing()