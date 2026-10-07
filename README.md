# CRM Analytics Engine — 2-Day Neo4j POC

This project implements the 2-day POC described in the supplied plan:

CRM Data -> Python -> Neo4j -> Graph Analytics -> Recommendation/Prediction -> FastAPI -> Streamlit

## What the POC demonstrates

- Employee/domain performance
- Domain similarity
- Employee similarity
- Customer similarity
- Domain recommendations with explainability
- Opportunity conversion prediction
- Recommended salesperson ranking
- Business-facing Streamlit dashboard
- Neo4j graph exploration

## Project structure

```text
crm-analytics-poc/
├── data/
│   └── crm_data.csv
├── neo4j/
│   ├── constraints.cypher
│   └── queries.cypher
├── ingestion/
│   └── load_to_neo4j.py
├── analytics/
│   ├── employee_metrics.py
│   ├── domain_similarity.py
│   ├── employee_similarity.py
│   └── graph_analytics.py
├── recommendation/
│   └── recommender.py
├── prediction/
│   └── conversion_model.py
├── api/
│   ├── main.py
│   └── routes/
│       ├── employees.py
│       └── opportunities.py
├── dashboard/
│   └── app.py
├── requirements.txt
└── .env.example
```

## 1. Install

Python 3.11+ is recommended.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## 2. Start Neo4j

Use Neo4j Desktop or Neo4j Docker.

Example Docker:

```bash
docker run --name crm-neo4j ^
  -p 7474:7474 -p 7687:7687 ^
  -d ^
  -e NEO4J_AUTH=neo4j/password ^
  neo4j:5
```

For Linux/macOS, replace `^` with `\`.

Copy `.env.example` to `.env` and change the credentials if necessary.

## 3. Create constraints

Run `neo4j/constraints.cypher` in Neo4j Browser.

## 4. Load CRM data

```bash
python ingestion/load_to_neo4j.py
```

This loads the consolidated `data/crm_data.csv` dataset.

## 5. Run analytics

```bash
python analytics/graph_analytics.py
```

## 6. Start FastAPI

From the project root:

```bash
uvicorn api.main:app --reload --port 8000
```

Swagger:

http://localhost:8000/docs

## 7. Start Streamlit

Open a second terminal:

```bash
streamlit run dashboard/app.py
```

## Main API endpoints

- `GET /employees`
- `GET /employees/{id}/performance`
- `GET /employees/{id}/recommendations`
- `GET /opportunities/{id}/prediction`
- `GET /opportunities/{id}/recommended-salespeople`

## POC recommendation formula

The recommendation score follows the supplied POC plan:

- 50% domain similarity
- 30% similar salesperson success
- 20% employee historical performance

## Conversion prediction

The POC uses an interpretable Logistic Regression model with:

- employee win rate
- employee domain win rate
- customer similarity
- interaction count
- meeting count
- days in current stage
- domain similarity
- previous customer interactions

## Important

This is a POC, not a production CRM platform. It intentionally excludes Kafka, Spark, Airflow, Kubernetes, real-time CDC, complex microservices, LLM agents, vector search, advanced deep learning, and production authentication.
