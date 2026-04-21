import subprocess
import duckdb
import os
import json
import logging
from datetime import datetime
from src.common_func.config import OPS_DB, SILVER_DB, LOG_DIR

logger = logging.getLogger(__name__)

# --- 1. LOGGING CONFIG ---
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'collection_audit.jsonl'),
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
)

def log_to_jsonl(level, module, message_dict):
    """Structured logging for JSONL parsing."""
    log_msg = json.dumps(message_dict)
    if level == "INFO":
        logging.info(log_msg, extra={'custom_module': module})
    elif level == "ERROR":
        logging.error(log_msg, extra={'custom_module': module})

# --- 2. ATOMIC GOVERNANCE ---
def report_governance(con, run_id, file_name, status, details, ops_db_path):
    """ATOMIC HANDOFF: Attaches Ops DB, inserts one audit record, and detaches."""
    con.execute(f"ATTACH '{ops_db_path}' AS target_ops")
    try:
        con.execute("""
            INSERT INTO target_ops.ingestion_audit (run_id, file_name, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, file_name, status, json.dumps(details), datetime.now()))
    finally:
        con.execute("DETACH target_ops")

# --- 3. SILVER TRANSFORMATION ENGINE ---
def run_vault_update():
    run_id = f"DBT_SILVER_{datetime.now().strftime('%Y%m%d_%H%M')}"
    start_time = datetime.now()
    con = duckdb.connect(':memory:')
    # Define the absolute path to your dbt project folder
    dbt_project_path = "/home/kaushik/pi-margin/pi_margin_dbt"

    try:
        # Run dbt silently (stateless parquet creation)
        result = subprocess.run(["dbt", "run"], cwd=dbt_project_path,capture_output=True, text=True, check=True)
        log_to_jsonl("INFO", "silver_handoff", {"event": "dbt_run_complete", "run_id": run_id})
        if result.returncode != 0:
                # This will put the ACTUAL dbt error into logs
                logger.error({"event": "failed", "error": result.stderr or result.stdout})
        else:
                # Proceed to move parquet to silver
                pass
    
        # Atomic Handoff to Silver
        con.execute(f"ATTACH '{SILVER_DB}' AS silver")
        con.execute("BEGIN TRANSACTION;")
        
        # Hub Update (Idempotent)
        con.execute("""
                INSERT INTO silver.hub_commodity
                SELECT 
                    CAST(hub_commodity_key AS VARCHAR), 
                    commodity_id, 
                    load_timestamp, 
                    record_source
                FROM '/home/kaushik/pi-margin/data/silver/hub_commodity.parquet'
                WHERE CAST(hub_commodity_key AS VARCHAR) NOT IN (
                    -- Added 'silver.' here
                    SELECT CAST(hub_commodity_key AS VARCHAR) FROM silver.hub_commodity
                );
        """)
        
        # Satellite Update (Historical/Idempotent via hash_diff)
        con.execute("""
            INSERT INTO silver.sat_commodity_prices 
            SELECT 
                CAST(hub_commodity_key AS VARCHAR), 
                CAST(hash_diff AS VARCHAR), 
                open_price, 
                high_price, 
                low_price, 
                close_price, 
                volume, 
                load_timestamp, 
                record_source
            FROM '/home/kaushik/pi-margin/data/silver/sat_commodity_prices.parquet'
            WHERE CAST(hash_diff AS VARCHAR) NOT IN (
                SELECT CAST(hash_diff AS VARCHAR) FROM silver.sat_commodity_prices
            );
        """)
        
        con.execute("COMMIT;")
        con.execute("DETACH silver")
        
        # Report back to Ops DB
        duration = (datetime.now() - start_time).total_seconds()
        report_governance(con, run_id, "silver_vault", "SUCCESS", {"duration_sec": duration}, OPS_DB)
        log_to_jsonl("INFO", "silver_handoff", {"status": "success", "duration": duration})
    except subprocess.CalledProcessError as e:
        # This is the secret sauce to find the error
        log_to_jsonl("ERROR", "silver_handoff", {"event": "failed", "error": e.stderr})
    except Exception as e:
        error_msg = str(e.stderr) if hasattr(e, 'stderr') else str(e)
        log_to_jsonl("ERROR", "silver_handoff", {"event": "failed", "error": error_msg})
        report_governance(con, run_id, "silver_vault", "FAILED", {"error": error_msg}, OPS_DB)
    finally:
        con.close()

if __name__ == "__main__":
    run_vault_update()