import subprocess
import duckdb
import logging
import os
from src.common_func.config import GOLD_DB, LOG_DIR

# Configure standard logging to JSONL
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'gold_audit.jsonl'),
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
)

def refine_gold_layer():
    logging.info("Starting dbt transformation sequence...")
    
    try:
        # 1. Hand over control to dbt
        # We capture stdout/stderr to write them to our log file instead of the screen
        result = subprocess.run(
            ['dbt', 'run', '--select', 'gold_rag_context'],
            cwd='/home/kaushik/pi-margin/pi_margin_dbt',
            capture_output=True,
            text=True,
            check=True
        )
        
        logging.info("dbt transformation complete.")
        logging.info(f"dbt Output Summary: {result.stdout}")

        # 2. Database Verification
        con = duckdb.connect(GOLD_DB)
        count = con.execute("SELECT count(*) FROM gold_rag_context").fetchone()[0]
        logging.info(f"Gold Layer Verified: {count} chunks ready in the database.")

    except subprocess.CalledProcessError as e:
        logging.error(f"dbt failed with exit code {e.returncode}")
        logging.error(f"dbt Error Log: {e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error in refinery: {str(e)}")

if __name__ == "__main__":
    refine_gold_layer()