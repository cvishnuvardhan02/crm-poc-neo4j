@echo off
echo Starting CRM Analytics POC...
echo.
echo 1. Make sure Neo4j is running.
echo 2. Run: python ingestion\load_to_neo4j.py
echo 3. Run in terminal 1: uvicorn api.main:app --reload --port 8000
echo 4. Run in terminal 2: streamlit run dashboard\app.py
