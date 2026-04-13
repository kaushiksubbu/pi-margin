import os

# --- Database Paths (Shared with Sentinel-Pi) ---
# point to the absolute paths of existing project to maintain a single source of truth
BASE_SENTINEL_DATA = '/mnt/data/sentinel-pi/data'

BRONZE_DB    = os.path.join(BASE_SENTINEL_DATA, 'bronze/raw_source.db')
SILVER_DB    = os.path.join(BASE_SENTINEL_DATA, 'silver/master_data.db')
GOLD_DB      = os.path.join(BASE_SENTINEL_DATA, 'gold/analytics.db')
REFERENCE_DB = os.path.join(BASE_SENTINEL_DATA, 'reference/reference.db')
OPS_DB       = os.path.join(BASE_SENTINEL_DATA, 'ops/ops.db')

# --- Project Local Paths ---
PROJECT_ROOT = '/home/kaushik/pi-margin'
LANDING_ZONE = os.path.join(PROJECT_ROOT, 'data/landing_zone')
LOG_DIR      = os.path.join(PROJECT_ROOT, 'logs')

# --- External APIs (Margin Specific) ---
# Tickers for Dutch Gas and Energy
TTF_GAS_TICKER = "TTF=F"
CBS_API_URL    = "https://opendata.cbs.nl/ODataApi/v1/"

# --- AI & Lineage ---
OLLAMA_MODEL = "llama3.2:1b-instruct-q4_K_M"
LINEAGE_FILE = os.path.join(PROJECT_ROOT, 'src/lineage/lineage_events.json')

# --- Constants ---
PI_MARGIN_SCHEMA = "margin_retail"