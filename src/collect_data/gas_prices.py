import yfinance as yf
import json
import logging
from datetime import datetime
from pydantic import ValidationError
import duckdb

from src.common_func.config import OPS_DB, BRONZE_DB, LOG_FILE_PATH 
from src.collect_data.contracts import GasPriceRecord
from src.common_func.db_utils import transform_record_for_ingestion

# Configure standard logging to JSONL
logging.basicConfig(
    filename=LOG_FILE_PATH,
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

def report_governance(source, event_type, details):
    """Writes drift and status to OPS_DB for AI/RAG auditability."""
    try:
        with duckdb.connect(OPS_DB) as con:
            con.execute("""
                INSERT INTO drift_events (source_name, event_type, details)
                VALUES (?, ?, ?)
            """, (source, event_type, json.dumps(details)))
    except Exception as e:
        # Fallback to JSONL if the OPS_DB itself is locked or failing
        log_to_jsonl("ERROR", "governance", {"event": "ops_db_fail", "error": str(e)})

def save_to_bronze(validated_records: list):
    """The clean write: No prints, only DB state changes and logs."""
    if not validated_records:
        return

    try:
        clean_data = [transform_record_for_ingestion(r) for r in validated_records]
        
        with duckdb.connect(BRONZE_DB) as con:
            con.register('clean_data_view', clean_data)
            con.execute("""
                INSERT INTO gas_prices_raw 
                SELECT * FROM clean_data_view
            """)
        
        log_to_jsonl("INFO", "ingestion", {"source": "TTF_GAS", "status": "success", "rows": len(clean_data)})
        
    except Exception as e:
        log_to_jsonl("ERROR", "ingestion", {"source": "TTF_GAS", "status": "fail", "error": str(e)})
        report_governance("TTF_GAS", "INGESTION_ERROR", {"error": str(e)})

def fetch_ttf_gas_prices():
    """Silent fetch with Contract Enforcement."""
    try:
        ticker = yf.Ticker("TTF=F")
        df = ticker.history(period="1d")
        
        if df.empty:
            log_to_jsonl("INFO", "fetch", {"source": "TTF_GAS", "message": "API returned empty dataframe"})
            return []
            
        latest = df.iloc[-1]
        
        try:
            record = GasPriceRecord(
                timestamp=datetime.now(),
                commodity="TTF_GAS",
                price_close=round(float(latest['Close']), 2),
                volume=int(latest['Volume']),
                currency="EUR"
            )
            return [record]
            
        except ValidationError as ve:
            # Governance event for the DB + JSONL for the dev
            report_governance("TTF_GAS", "SCHEMA_DRIFT", ve.errors())
            log_to_jsonl("ERROR", "contract", {"source": "TTF_GAS", "error": "validation_failed", "details": ve.errors()})
            return []

    except Exception as e:
        log_to_jsonl("ERROR", "fetch", {"source": "TTF_GAS", "error": str(e)})
        report_governance("TTF_GAS", "API_ERROR", {"error": str(e)})
        return []