import duckdb
from src.common_func.config import DB_DIR 
import os

def initialize_ops_db():
    ops_path = os.path.join(DB_DIR, "ops.db")
    con = duckdb.connect(ops_path)
    
    # The Registry Table
    con.execute("""
        CREATE TABLE IF NOT EXISTS schema_registry (
            source_name VARCHAR PRIMARY KEY,
            version INTEGER,
            schema_json JSON,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # The Drift Log 
    con.execute("""
        CREATE TABLE IF NOT EXISTS drift_events (
            event_id UUID DEFAULT gen_random_uuid(),
            source_name VARCHAR,
            event_type VARCHAR, -- 'BREAKING', 'ADDITIVE', 'TYPE_CHANGE'
            details JSON,
            resolved BOOLEAN DEFAULT FALSE
        )
    """)
    con.close()
    print("Ops Database & Schema Registry initialized.")