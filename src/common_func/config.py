import os

# Base project directory (where your venv and src live)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The root folder for ALL your Sentinel data
# This is where your bronze, silver, gold, and ops folders will sit
BASE_SENTINEL_DATA = os.path.join(BASE_DIR, 'data')

# The specific directory for DuckDB files
DB_DIR = os.path.join(BASE_SENTINEL_DATA, 'databases')

# Ensure the DB_DIR exists so scripts don't crash
os.makedirs(DB_DIR, exist_ok=True)

# Update your specific DB paths to use the new DB_DIR
BRONZE_DB    = os.path.join(DB_DIR, 'raw_source.db')
SILVER_DB    = os.path.join(DB_DIR, 'master_data.db')
GOLD_DB      = os.path.join(DB_DIR, 'analytics.db')
REFERENCE_DB = os.path.join(DB_DIR, 'reference.db')
OPS_DB       = os.path.join(DB_DIR, 'ops.db')

# --- Project Local Paths ---
PROJECT_ROOT = '/home/kaushik/pi-margin'
LANDING_ZONE = os.path.join(PROJECT_ROOT, 'data/landing_zone')
LOG_DIR      = os.path.join(PROJECT_ROOT, 'logs')
LOG_FILE_PATH = os.path.join(LOG_DIR, 'sentinel_ingestion.jsonl')

# Use the variables SECOND
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(LANDING_ZONE, exist_ok=True)

# --- External APIs (Margin Specific) ---
# Tickers for Dutch Gas and Energy
TTF_GAS_TICKER = "TTF=F"
CBS_API_URL    = "https://opendata.cbs.nl/ODataApi/v1/"

# --- AI & Lineage ---
OLLAMA_MODEL = "llama3.2:1b-instruct-q4_K_M"
LINEAGE_FILE = os.path.join(PROJECT_ROOT, 'src/lineage/lineage_events.json')

# --- Constants ---
PI_MARGIN_SCHEMA = "margin_retail"

# OpenLineage Local Config
LINEAGE_LOG = os.path.join(LOG_DIR, 'openlineage_events.jsonl')

# Environmental variables for the OpenLineage Client
os.environ['OPENLINEAGE_URL'] = f"file://{LINEAGE_LOG}"
os.environ['OPENLINEAGE_NAMESPACE'] = "sentinel-pi-local"