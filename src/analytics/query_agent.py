import chromadb
from sentence_transformers import SentenceTransformer
import subprocess
import sys

def run_rag_query(user_query):
    print(f"\n🔍 Searching vector memory for: '{user_query}'...")
    
    # 1. Initialize the Librarian (Embedding Model)
    # Using the same model we used for ingestion
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(user_query).tolist()

    # 2. Connect to the Brain (ChromaDB)
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="margin_risk_context")
    
    # 3. Retrieve the top 3 most relevant "Gold" chunks
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=1
    )
    
    context_text = "\n".join(results['documents'][0])
    
    # 4. Feed to Llama 3.2 via Ollama
    # We pass the context + query as a structured prompt
    full_prompt = f"""
    You are a Commodity Risk AI. Use the context below to answer the user.
    If the data isn't there, be honest. Use bullet points for risk factors.

    CONTEXT:
    {context_text}

    USER QUESTION: {user_query}

    EXECUTIVE SUMMARY:
    """

    print("🧠 Llama 3.2 is generating report (this may take 30-60s on Pi)...")
    
    try:
        # Use subprocess to call Ollama directly - stays lean on RAM
        result = subprocess.run(
            ['ollama', 'run', 'llama3.2'],
            input=full_prompt,
            capture_output=True,
            text=True,
            check=True
        )
        print("\n--- FINAL REPORT ---")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error calling Llama: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "Summarize the current risk for TTF_GAS. Is it Bullish or Bearish?"
    
    run_rag_query(query)