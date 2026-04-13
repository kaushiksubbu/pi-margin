ADR ID,Title,Status,Summary
# 001,Platform Choice
Status - Implemented
RPi4 Edge node for high-governance local execution.
# 002,Data Architecture
Status - Accepted
Hybrid Medallion (Raw/Silver/Gold) + Data Vault 2.0 (Hub/Sat).
# 003,Storage Strategy
Status - Implemented
Shared DuckDB across PI Suite via /mnt/data/ absolute paths.
# 004,Governance
Status - Accepted
Lean Observability via ops.db (JSON events) + SODA Core gates.
# 005,Modular Standards
Status - Accepted
Unified src/ layout across all projects to enable code reuse.
# 006: Orchestration & Portability 
Status - Draft
Decision: Use Prefect for workflow management and Docker for environmental isolation.

Rationale: Prefect handles the "hidden" logic of data engineering (retries, timeouts). Docker ensures that library conflicts (like yfinance dependencies) don't break the system Python on the RPi4.