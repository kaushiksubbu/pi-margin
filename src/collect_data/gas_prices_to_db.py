import os
import json
import uuid
import logging
import duckdb
from datetime import datetime
from pydantic import ValidationError

from src.common_func.config import OPS_DB, BRONZE_DB, LOG_DIR, LANDING_ZONE
from src.common_func.contracts import GasPriceRecord

# --- 1. THE LOGGING HEARTBEAT ---
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'collection_audit.jsonl'),
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
)

def log_to_jsonl(level, module, message_dict):
    """Structured logging for JSONL parsing."""
    log_msg = json.dumps(message_dict)
    if level == "INFO":
        logging.info(log_msg)
    elif level == "ERROR":
        logging.error(log_msg)

def report_governance(con_ops, run_id, file_name, status, details):
    """Writes to ingestion_audit for RAG/AI traceability."""
    con_ops.execute("""
        INSERT INTO ingestion_audit (run_id, file_name, status, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, file_name, status, json.dumps(details), datetime.now()))

# --- 2. THE INGESTION ENGINE ---
def run_ingestion():
    files = [f for f in os.listdir(LANDING_ZONE) if f.endswith('.json')]
    run_id = str(uuid.uuid4())

    if not files:
        log_to_jsonl("INFO", "ingestor", {"event": "skip", "reason": "empty_landing_zone"})
        return

    con_bronze = duckdb.connect(BRONZE_DB)
    con_ops = duckdb.connect(OPS_DB)

    for file_name in files:
        file_path = os.path.join(LANDING_ZONE, file_name)
        rows_processed = 0
        drift_detected = False
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    raw_data = json.loads(line)
                    try:
                        # Pydantic Validation
                        record = GasPriceRecord(**raw_data)
                        
                        # --- 3. DRIFT DETECTION ---
                        # model_extra contains fields not defined in the class
                        extra_fields = record.model_extra if hasattr(record, 'model_extra') else {}
                        if extra_fields:
                            drift_detected = True
                            log_to_jsonl("INFO", "drift", {"file": file_name, "new_fields": list(extra_fields.keys())})

                        # --- 4. IDEMPOTENT INSERT ---
                        con_bronze.execute("""
                            INSERT INTO gas_prices_raw 
                            SELECT ? as commodity, ? as close_price, ? as volume, ? as timestamp, ? as metadata
                            WHERE NOT EXISTS (
                                SELECT 1 FROM gas_prices_raw 
                                WHERE commodity = ? AND timestamp = ?
                            )
                        """, (record.commodity, record.Close, record.Volume, record.timestamp, 
                              json.dumps(extra_fields), record.commodity, record.timestamp))
                        rows_processed += 1

                    except ValidationError as ve:
                        log_to_jsonl("ERROR", "contract", {"file": file_name, "error": ve.errors()})

            # Success Logging
            report_governance(con_ops, run_id, file_name, "SUCCESS", {"rows": rows_processed, "drift": drift_detected})
            log_to_jsonl("INFO", "ingestion", {"file": file_name, "status": "success", "rows": rows_processed})

        except Exception as e:
            # Error Recovery
            log_to_jsonl("ERROR", "ingestion", {"file": file_name, "error": str(e)})
            report_governance(con_ops, run_id, file_name, "FAILED", {"error": str(e)})
        
    con_bronze.close()
    con_ops.close()

if __name__ == "__main__":
    run_ingestion()