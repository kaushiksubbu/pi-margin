import os
import json
import uuid
import logging
import duckdb
from datetime import datetime
from pydantic import ValidationError

from src.common_func.config import OPS_DB, BRONZE_DB, LOG_DIR, LANDING_ZONE
from src.common_func.contracts import GasPriceRecord

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

def report_governance(con, run_id, file_name, status, details, ops_db_path):
    """
    ATOMIC HANDOFF: Attaches Ops DB, inserts one audit record, and detaches.
    This minimizes lock time so other processes can read ops.db.
    """
    con.execute(f"ATTACH '{ops_db_path}' AS target_ops")
    try:
        con.execute("""
            INSERT INTO target_ops.ingestion_audit (run_id, file_name, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, file_name, status, json.dumps(details), datetime.now()))
    finally:
        con.execute("DETACH target_ops")

# --- 2. THE INGESTION ENGINE ---
def run_ingestion():
    files = [f for f in os.listdir(LANDING_ZONE) if f.endswith('.json')]
    run_id = str(uuid.uuid4())
    
    if not files:
        log_to_jsonl("INFO", "ingestor", {"event": "skip", "reason": "empty_landing_zone"})
        return

    # Use an in-memory connection as our 'orchestrator'
    con = duckdb.connect(':memory:')

    for file_name in files:
        file_path = os.path.join(LANDING_ZONE, file_name)
        rows_processed = 0
        drift_detected = False
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    raw_data = json.loads(line)
                    try:
                        # Pydantic Validation & Contract Enforcement
                        record = GasPriceRecord(**raw_data)
                        
                        # Drift Detection (extra fields from 'allow' config)
                        extra_fields = record.model_extra if hasattr(record, 'model_extra') else {}
                        if extra_fields:
                            drift_detected = True
                            log_to_jsonl("INFO", "drift", {"file": file_name, "new_fields": list(extra_fields.keys())})
                            
                        # ATOMIC HANDOFF TO BRONZE
                        con.execute(f"ATTACH '{BRONZE_DB}' AS target_bronze")
                        try:
                            con.execute("""
                                INSERT INTO target_bronze.gas_prices_raw 
                                SELECT ? as symbol, ? as close_price, ? as volume, ? as timestamp, ? as metadata
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM target_bronze.gas_prices_raw 
                                    WHERE symbol = ? AND timestamp = ?
                                )
                            """, (record.commodity, record.Close, record.Volume, record.timestamp, 
                                  json.dumps(extra_fields), record.commodity, record.timestamp))
                        finally:
                            con.execute("DETACH target_bronze")
                        
                        rows_processed += 1

                    except ValidationError as ve:
                        log_to_jsonl("ERROR", "contract validation", {"file": file_name, "error": "validation_failed", "details": ve.errors()})

            # Success: Atomic Handoff to Ops
            report_governance(con, run_id, file_name, "SUCCESS", 
                              {"rows": rows_processed, "drift": drift_detected}, OPS_DB)
            log_to_jsonl("INFO", "ingestion", {"file": file_name, "status": "success", "rows": rows_processed})

        except Exception as e:
            # Error: Atomic Handoff to Ops
            log_to_jsonl("ERROR", "ingestion", {"file": file_name, "error": str(e)})
            report_governance(con, run_id, file_name, "FAILED", {"error": str(e)}, OPS_DB)
        
    con.close()

if __name__ == "__main__":
    run_ingestion()