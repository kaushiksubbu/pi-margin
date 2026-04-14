### Key Decisions
# 001,Platform Choice
RPi4 Edge node for high-governance local execution.
# 002,Data Architecture
Hybrid Medallion (Raw/Silver/Gold) + Data Vault 2.0 (Hub/Sat).
# 003,Storage Strategy
Shared DuckDB+Parquet across PI Suite via /mnt/data/ absolute paths.
# 004,Governance
Lean Observability via ops.db (JSON events) + SODA Core gates.
# 005,Modular Standards
Unified src/ layout across all projects to enable code reuse.
# 006: Orchestration & Portability 
Decision: Use Prefect for workflow management and Docker for environmental isolation.
Rationale: Prefect handles the "hidden" logic of data engineering (retries, timeouts). Docker ensures that library conflicts (like yfinance dependencies) don't break the system Python on the RPi4.

# ADR 001: Decoupled Landing Zone Architecture
Date: 2026-04-14
Status: Accepted

Context
We need to collect high-frequency market data (TTF Gas) on a Raspberry Pi 4. Direct insertion from API to Database is risky if the DB is locked or the schema changes unexpectedly.

Decision
We will use a Landing Zone Pattern.

A "Dumb" Collector fetches raw JSON and appends it to a daily .jsonl file.

A "Smart" Ingestor (to be finished tomorrow) reads the file, validates it, and moves it to DuckDB.

Consequences
Positive: Resilience against DB downtime; ability to "replay" raw data if logic changes; bypasses API rate limits during testing.

Negative: Requires a small amount of extra disk space for the raw files (negligible for this scale).

# ADR 002: "Dynamic Contract" for Schema Drift
Status: Accepted

Decision
Use Pydantic's extra='allow' combined with a dedicated metadata JSON column in DuckDB.

Rationale
Market APIs frequently add new fields (e.g., vix_index, trade_status). Instead of crashing the pipeline or ignoring the data, we "quarantine" these unknown fields into a JSON bucket. This keeps the Bronze Layer stable while preserving 100% of the incoming data for future AI discovery.

Since we are using OpenLineage via FileTransport, your Lineage ADR needs to specify how we capture the "story" of a data point without a central server. This ADR ensures that every byte in your DuckDB can be traced back to its raw JSON source.

# ADR-003: Traceable Lineage via Metadata Injection
Date: 2026-04-14

Status: Accepted 
Context
As data moves from the internet to the Gold layer, we need a way to debug "Bad Data" and perform audit trails. If a margin calculation looks wrong, we must be able to prove if the error was in the source API, the Pydantic validation, or the SQL transformation. Standard logging (JSONL) is useful for errors but lacks the "Dataset-to-Dataset" relationship needed for true observability.

Decision
We will implement OpenLineage-compliant metadata injection using a two-pronged approach:

Local Metadata Injection (The "Passport"): Every row inserted into DuckDB will include a lineage_id or source_file reference.

OpenLineage Events (The "Flight Recorder"): We will use the openlineage-python library configured with FileTransport to emit JSON events to logs/openlineage_events.jsonl.

Technical Implementation
No JVM: We explicitly reject the use of a Marquez/JVM server to save RPi resources.

File-Based: All lineage events are appended to a local .jsonl file.

Dataset Naming: * Inputs: yfinance://TTF=F or file://data/landing_zone/ttf_gas_YYYYMMDD.jsonl

Outputs: file://data/landing_zone/... or duckdb://raw_source.db/gas_prices_raw

Consequences
Positive: High Observability. We can use DuckDB to query our own lineage logs to see how long jobs took and how many rows were moved.

Positive: Audit Ready. Meets institutional standards for data provenance.

Negative: Manual Instrumentation. We must manually add "Start" and "Complete" emitters to our Python functions (this will be done in tomorrow's session).

Negative: Log Rotation. The openlineage_events.jsonl will grow over time and will eventually need a cleanup strategy.