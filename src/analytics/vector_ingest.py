import duckdb
import chromadb
import json
import os
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer
from src.common_func.config import LANDING_ZONE, LOG_DIR

# Configure standard logging to JSONL (matches your collection pattern)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'vector_ingest_audit.jsonl'),
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
)

def log_to_jsonl(level, module, message_dict):
    """Structured logging for file-based debugging (Reused from your template)."""
    log_msg = json.dumps(message_dict)
    if level == "INFO":
        logging.info(log_msg)
    elif level == "ERROR":
        logging.error(log_msg)

def ingest_to_chroma():
    try:
        # 1. Initialize DB Connection
        # Replicating your manual fix: Attach master_data as silver
        con = duckdb.connect('/home/kaushik/pi-margin/data/databases/analytics.db')
        con.execute(f"ATTACH '/home/kaushik/pi-margin/data/databases/master_data.db' AS silver;")

        # 2. Fetch Gold Data
        df = con.execute("SELECT chunk_text, commodity_id FROM gold_rag_context").fetchdf()
        
        if df.empty:
            log_to_jsonl("INFO", "ingest", {"status": "empty", "message": "No data found in gold_rag_context"})
            return

        # 3. Load Embedding Model
        # Using the Librarian model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # 4. Setup ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(name="margin_risk_context")

        # 5. Ingest Data
        # use the index for unique IDs and chunk_text for the vector data
        documents = df['chunk_text'].tolist()
        metadatas = [{"commodity": cid} for cid in df['commodity_id'].tolist()]
        ids = [f"id_{i}_{datetime.now().strftime('%Y%m%d')}" for i in range(len(documents))]

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        log_to_jsonl("INFO", "ingest", {
            "status": "success", 
            "items_ingested": len(documents),
            "collection": "margin_risk_context"
        })
        
        print(f"Ingested {len(documents)} chunks into ChromaDB.")

    except Exception as e:
        log_to_jsonl("ERROR", "ingest", {"status": "failed", "error": str(e)})
        print(f"Ingestion failed. Check logs.")

if __name__ == "__main__":
    ingest_to_chroma()