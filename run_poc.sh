#!/bin/bash
echo "Starting CRM Analytics POC..."
echo "1. Make sure Neo4j is running."
echo "2. Run: python ingestion/load_to_neo4j.py"
echo "3. Terminal 1: uvicorn api.main:app --reload --port 8000"
echo "4. Terminal 2: streamlit run dashboard/app.py"
