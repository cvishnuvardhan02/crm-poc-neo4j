# CRM Analytics Engine --- Graph Intelligence POC

A Proof of Concept (POC) for CRM analytics using **Neo4j**, **FastAPI**,
and **Streamlit**. The application models CRM records as a graph,
calculates semantic similarity between domains, and ranks salespeople
for an opportunity using graph-derived evidence and historical
performance.

> **Important:** The displayed *Likelihood Score* is a weighted
> recommendation score, not a calibrated statistical probability of
> conversion. Production use requires historical validation,
> calibration, security hardening, and operational testing.

## Contents

-   [Overview](#overview)
-   [Features](#features)
-   [Architecture](#architecture)
-   [Technology stack](#technology-stack)
-   [Graph data model](#graph-data-model)
-   [Recommendation logic](#recommendation-logic)
-   [Domain similarity and cold
    start](#domain-similarity-and-cold-start)
-   [Project structure](#project-structure)
-   [Setup and run locally](#setup-and-run-locally)
-   [API endpoints](#api-endpoints)
-   [Create an opportunity](#create-an-opportunity)
-   [Verify data in Neo4j](#verify-data-in-neo4j)
-   [Dashboard tabs](#dashboard-tabs)
-   [Testing checklist](#testing-checklist)
-   [Limitations and production
    considerations](#limitations-and-production-considerations)
-   [Troubleshooting](#troubleshooting)

## Overview

Traditional CRM data is commonly stored in tables, but questions such as
*"Which salesperson has experience in a domain similar to this new
opportunity?"* depend on relationships across employees, opportunities,
customers, products, stages, and domains.

This POC represents those entities as nodes and their business
connections as relationships in Neo4j. A Python backend retrieves graph
evidence and calculates recommendations. The Streamlit interface
presents results as metrics, tables, explanations, and an interactive
graph.

### Goals

-   Represent CRM entities and relationships in a graph.
-   Identify related domains using semantic embeddings rather than
    hardcoded mappings.
-   Rank salespeople using domain relevance, peer success, and
    historical performance.
-   Explain recommendations with supporting graph and performance
    evidence.
-   Support newly introduced domains through similarity updates and a
    cold-start fallback.
-   Provide an interactive dashboard for CRM analytics and graph
    exploration.

## Features

-   **Executive Dashboard** --- high-level CRM and sales metrics.
-   **Salesperson Analytics** --- wins, losses, win rate, opportunities,
    and revenue won.
-   **Recommendations** --- ranked recommendations and component scores.
-   **Create Opportunity** --- create an opportunity and connect it to
    its customer and domain.
-   **Opportunity Intelligence** --- inspect an opportunity and
    salesperson ranking.
-   **Graph Explorer** --- explore Neo4j nodes and relationships.
-   **Semantic Domain Similarity** --- use `all-MiniLM-L6-v2` embeddings
    to compare domain text.
-   **Confidence-adjusted performance** --- shrink small-sample win
    rates toward the team baseline.
-   **Cold-start handling** --- use a company-wide baseline when
    domain-specific peer evidence is unavailable.
-   **Evidence tables** --- show domain and peer evidence behind
    recommendations.

## Architecture

``` text
User / Sales Manager
        |
        v
Streamlit UI (app.py)
  - dashboard tabs
  - forms, metrics, tables and graph
        |
        | HTTP requests
        v
FastAPI backend
  - opportunity routes
  - domain routes
  - recommendation routes
  - graph queries
        |
        v
Python services
  - Neo4j reads/writes
  - semantic similarity
  - weighted recommendation scoring
  - evidence generation
        |
        | Bolt / Cypher
        v
Neo4j database
  - CRM nodes
  - business relationships
  - SIMILAR_TO domain links
```

**Request flow**

1.  A user selects an opportunity or enters a new one in Streamlit.
2.  Streamlit sends an HTTP request to FastAPI.
3.  FastAPI validates the request and calls the relevant service.
4.  The service reads or writes nodes and relationships in Neo4j.
5.  For recommendations, the service gathers domain evidence, peer
    success, and historical performance.
6.  FastAPI returns structured JSON.
7.  Streamlit renders the response as metrics, tables, explanations, and
    a graph.

## Technology stack

  Technology              Purpose
  ----------------------- -------------------------------------------
  Python                  Backend and application logic
  Streamlit               Interactive dashboard
  FastAPI                 REST API layer
  Neo4j                   Graph database and relationship traversal
  Cypher                  Neo4j query language
  Sentence Transformers   Domain text embeddings
  `all-MiniLM-L6-v2`      Semantic embedding model
  Cosine similarity       Compare embedding vectors
  Plotly                  Interactive graph visualization
  Pandas / NumPy          Data shaping and numeric operations
  `python-dotenv`         Load local environment configuration

## Graph data model

Neo4j represents business entities as **nodes** and their connections as
typed **relationships**.

### Node labels

  Node            Meaning
  --------------- -------------------------------------------
  `Employee`      Salesperson
  `Opportunity`   Sales deal or pipeline item
  `Customer`      Customer or account
  `Domain`        Business or technical domain
  `Product`       Product or service associated with a deal
  `Stage`         Opportunity pipeline stage
  `Interaction`   Sales activity or interaction
  `Industry`      Industry classification, where present

### Relationship types

  --------------------------------------------------------------------------
  Relationship            Typical direction          Meaning
  ----------------------- -------------------------- -----------------------
  `OWNS`                  `Employee → Opportunity`   Employee owns or is
                                                     assigned to an
                                                     opportunity

  `TARGETS`               `Opportunity → Domain`     Opportunity targets a
                                                     domain

  `FOR_CUSTOMER`          `Opportunity → Customer`   Opportunity relates to
                                                     a customer

  `FOR_PRODUCT`           `Opportunity → Product`    Opportunity relates to
                                                     a product

  `AT_STAGE`              `Opportunity → Stage`      Opportunity is at a
                                                     pipeline stage

  `PERFORMED`             `Employee → Interaction`   Employee performed an
                                                     interaction

  `WITH`                  `Interaction → Customer`   Interaction involved a
                                                     customer

  `SIMILAR_TO`            `Domain ↔ Domain`          Domains have a semantic
                                                     similarity score
  --------------------------------------------------------------------------

Relationship directions should be confirmed against the current graph
schema if the implementation changes.

### Why use a graph?

A recommendation can traverse from an employee to their opportunities
and then to the domains those opportunities target. The engine can
compare those domains with a target opportunity's domain and use stored
`SIMILAR_TO` edges to include related-domain evidence.

A node existing in Neo4j does not automatically mean all expected
relationships exist. An opportunity can be persisted while its
salesperson assignment is missing if the `OWNS` relationship was not
written.

## Recommendation logic

The POC combines three components into a weighted score:

``` text
Recommendation Score =
    0.50 × Domain Similarity
  + 0.30 × Peer Success
  + 0.20 × Historical Performance
```

  ------------------------------------------------------------------------
  Component                                   Weight Interpretation
  --------------------- ---------------------------- ---------------------
  Domain Similarity                              50% Relevance of the
                                                     salesperson's
                                                     successful domain
                                                     experience to the
                                                     target domain,
                                                     including
                                                     related-domain graph
                                                     evidence

  Peer Success                                   30% Success signal from
                                                     relevant outcomes in
                                                     the target or related
                                                     domains

  Historical                                     20% Salesperson's
  Performance                                        closed-opportunity
                                                     performance, adjusted
                                                     for small samples
  ------------------------------------------------------------------------

The components are normalized to a 0--1 scale before weighting. The
result is used to rank salespeople.

### Win rate

The raw historical win rate is calculated from closed opportunities:

``` text
Raw Win Rate = Wins / (Wins + Losses)
```

Open opportunities are excluded because their outcomes are not yet
known.

### Confidence-adjusted historical performance

A perfect record from one deal should not automatically outweigh a
larger, more informative history. The POC uses prior-based smoothing:

``` text
Adjusted Performance =
    (Wins + Team Baseline × Prior Strength)
    / (Closed Opportunities + Prior Strength)
```

The implementation uses a prior strength of `5`. The team baseline is
the overall win rate across closed opportunities. As a salesperson
accumulates more closed deals, their own outcomes have more influence on
the adjusted score.

This is a practical smoothing heuristic, not a formal confidence
interval.

> The *Likelihood Score* is currently a weighted recommendation score,
> not a statistically calibrated probability that an opportunity will be
> won. Calling it a conversion probability would require historical
> backtesting and calibration.

## Domain similarity and cold start

### Semantic similarity workflow

1.  Retrieve domain text from Neo4j.
2.  Encode each domain using `all-MiniLM-L6-v2`.
3.  Compare embedding vectors using cosine similarity.
4.  Apply the configured similarity threshold.
5.  Create or update `SIMILAR_TO` relationships with a score.
6.  Retrieve those relationships when ranking salespeople for an
    opportunity.

Cosine similarity compares the direction of two vectors. Higher values
indicate more similar text representations, but semantic similarity does
not guarantee that two domains are interchangeable in a business
context.

### Adding a new domain

Creating an opportunity can create or reuse a `Domain` node. The
similarity workflow must then run to compare the new domain with
existing domains and store relevant edges. A new domain node alone does
not guarantee that similarity relationships exist.

Known domain routes:

  -------------------------------------------------------------------------------------
  Method                  Endpoint                              Purpose
  ----------------------- ------------------------------------- -----------------------
  `GET`                   `/domains`                            List known domains

  `POST`                  `/domains/embeddings/build`           Build or refresh domain
                                                                embeddings

  `POST`                  `/domains/similarity/build`           Build similarity
                                                                relationships across
                                                                domains

  `POST`                  `/domains/{domain_name}/similarity`   Update similarity
                                                                relationships for one
                                                                domain

  `GET`                   `/domains/{domain_name}/similar`      Retrieve similar
                                                                domains and scores
  -------------------------------------------------------------------------------------

### Cold-start fallback

A cold-start domain has no usable domain-specific peer evidence. In that
case, the recommendation flow can use the company-wide historical
win-rate baseline for the peer-success component while continuing to use
any available employee performance and semantic-domain evidence.

The implementation should distinguish between: - no peer evidence
exists; and - peer evidence exists, but there were no wins.

These situations have different meanings and should not be treated as
equivalent.

## Project structure

The exact structure may vary by branch. The main files and folders used
by the POC include:

``` text
crm-analytics-poc/
├── app.py
├── api/
│   ├── main.py
│   └── routes/
│       ├── domains.py
│       ├── opportunities.py
│       └── recommendations.py
├── services/
│   ├── domain_similarity.py
│   └── salesperson_recommendation.py
├── data/
│   └── crm_data.csv
├── .env
└── requirements.txt
```

Do not commit real credentials in `.env`. Keep secrets local or use a
secrets manager in a deployed environment.

## Setup and run locally

### Prerequisites

-   Python installed and available on your command line.
-   A running Neo4j instance (local installation or Docker).
-   The project source code and its Python dependencies.

Typical local endpoints: - Neo4j Bolt: `bolt://localhost:7687` -
FastAPI: `http://localhost:8000` - Streamlit: `http://localhost:8501`

### 1. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

### 2. Install dependencies

If the repository contains `requirements.txt`:

``` bash
pip install -r requirements.txt
```

If it does not, create one from the dependencies used by your project.
Check compatibility with your installed Python version before installing
packages.

### 3. Start Neo4j

Start the Neo4j service or Docker container and verify it is accessible
at the configured Bolt URI.

### 4. Configure environment variables

Create a `.env` file in the project root:

``` dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace_with_your_local_password
NEO4J_DATABASE=neo4j
API_BASE_URL=http://localhost:8000
```

Use your actual local password. **Never commit real credentials or a
populated `.env` file to GitHub.**

### 5. Start FastAPI

From the project root:

``` bash
uvicorn api.main:app --reload
```

Open: - Swagger UI: `http://localhost:8000/docs` - OpenAPI schema:
`http://localhost:8000/openapi.json`

### 6. Start Streamlit

Open a second terminal in the project root:

``` bash
python -m streamlit run app.py
```

Streamlit commonly opens at `http://localhost:8501`. Start the backend
before using UI features that make API requests.

## API endpoints

The known POC routes include the following. Use the running FastAPI
`/docs` page as the source of truth for current route definitions and
schemas.

  ---------------------------------------------------------------------------------------------------------------
  Method                  Endpoint                                                        Purpose
  ----------------------- --------------------------------------------------------------- -----------------------
  `GET`                   `/health/neo4j`                                                 Check the Neo4j
                                                                                          connection

  `GET`                   `/graph`                                                        Retrieve a graph
                                                                                          neighborhood for an
                                                                                          entity and traversal
                                                                                          depth

  `GET`                   `/domains`                                                      List known domains

  `POST`                  `/domains/embeddings/build`                                     Build or refresh domain
                                                                                          embeddings

  `POST`                  `/domains/similarity/build`                                     Build the domain
                                                                                          similarity graph

  `POST`                  `/domains/{domain_name}/similarity`                             Update similarity
                                                                                          relationships for a
                                                                                          domain

  `GET`                   `/domains/{domain_name}/similar`                                Retrieve similar
                                                                                          domains and scores

  `POST`                  `/opportunities`                                                Create an opportunity
                                                                                          and related entities

  `GET`                   `/recommendations/opportunities/{opportunity_id}/salespeople`   Rank salespeople for an
                                                                                          opportunity

  `GET`                   `/opportunities/{opportunity_id}/prediction`                    Retrieve the current
                                                                                          prediction/score
                                                                                          response, if enabled
  ---------------------------------------------------------------------------------------------------------------

The recommendation endpoint returns an opportunity identifier,
scoring-method/weight information, and a ranked salesperson list with
score components and evidence. Confirm exact response fields in the
current backend code.

## Create an opportunity

The create-opportunity request model includes `name`, `customer_name`,
`domain`, `value`, and optional `employee_id`.

Example request body:

``` json
{
  "name": "Quantum AI Platform",
  "customer_name": "ABC Technologies",
  "domain": "Quantum Computing",
  "value": 1000000,
  "employee_id": "E002"
}
```

Example API call:

``` bash
curl -X POST "http://localhost:8000/opportunities" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Quantum AI Platform\",\"customer_name\":\"ABC Technologies\",\"domain\":\"Quantum Computing\",\"value\":1000000,\"employee_id\":\"E002\"}"
```

The intended write flow is to: 1. Generate an opportunity ID. 2. Create
or reuse the Customer node. 3. Create or reuse the Domain node. 4.
Create the Opportunity node. 5. Create `FOR_CUSTOMER` and `TARGETS`
relationships. 6. Create `OWNS` if a valid employee ID is supplied.

**Recommendation and assignment are separate actions.** Returning a
recommended salesperson does not itself assign the opportunity.
Assignment must be persisted by the backend, usually through an `OWNS`
relationship.

## Verify data in Neo4j

Use Neo4j Browser to verify that an opportunity and its relationships
were saved. Adjust property names to match the canonical IDs in your
database.

### Inspect an opportunity and connected entities

``` cypher
MATCH (o:Opportunity)
WHERE o.name = $opportunity_name
OPTIONAL MATCH (e:Employee)-[:OWNS]->(o)
OPTIONAL MATCH (o)-[:FOR_CUSTOMER]->(c:Customer)
OPTIONAL MATCH (o)-[:TARGETS]->(d:Domain)
RETURN o, e, c, d;
```

Replace `$opportunity_name` with the opportunity name you created.

### Inspect a salesperson's opportunities

``` cypher
MATCH (e:Employee)-[:OWNS]->(o:Opportunity)
WHERE e.employee_id = $employee_id
RETURN e, o
ORDER BY o.name;
```

Update the employee identifier property if your graph uses a different
key.

### Inspect domain similarity relationships

``` cypher
MATCH (d:Domain)-[r:SIMILAR_TO]-(other:Domain)
WHERE toLower(d.name) = toLower($domain_name)
RETURN d.name AS domain,
       other.name AS similar_domain,
       r.score AS similarity
ORDER BY similarity DESC;
```

### Check the company-wide closed-deal baseline

``` cypher
MATCH (o:Opportunity)
WHERE o.outcome IN ['Won', 'Lost']
RETURN count(o) AS closed_opportunities,
       sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) AS wins;
```

## Dashboard tabs

  -----------------------------------------------------------------------
  Tab                                 Purpose
  ----------------------------------- -----------------------------------
  Executive Dashboard                 High-level CRM metrics

  Salesperson Analytics               Individual salesperson performance

  Recommendations                     Ranked recommendations and evidence

  Create Opportunity                  Create an opportunity and trigger
                                      related workflows

  Opportunity Intelligence            Inspect a selected opportunity and
                                      its ranking

  Graph Explorer                      Explore graph nodes, relationships
                                      and connected entities
  -----------------------------------------------------------------------

### Graph Explorer notes

-   Node colors represent entity types.
-   Traversal depth controls how far the graph query follows
    relationships.
-   Employee-to-employee connections may be inferred from shared
    domains, similar domains, shared customers, or shared wins.
-   Inferred visualization links are not necessarily direct
    employee-to-employee relationships stored in Neo4j.
-   A relationship cannot be drawn if it is absent from the graph
    response returned by the backend.
-   Large graph neighborhoods can become visually dense; use labels and
    filters carefully.

## Testing checklist

Before presenting the POC, verify:

-   [ ] `GET /health/neo4j` succeeds.
-   [ ] FastAPI starts without import errors.
-   [ ] Streamlit starts and all dashboard tabs load.
-   [ ] Existing opportunities can be selected and inspected.
-   [ ] Creating an opportunity persists its Opportunity node.
-   [ ] Customer and Domain nodes are created or reused as expected.
-   [ ] `FOR_CUSTOMER` and `TARGETS` relationships exist.
-   [ ] If an employee is assigned, `Employee -[:OWNS]-> Opportunity`
    exists.
-   [ ] The new-domain similarity workflow runs and its results can be
    retrieved.
-   [ ] Recommendations return scores and supporting evidence.
-   [ ] Cold-start behavior is identified when domain-specific peer
    evidence is missing.
-   [ ] Graph Explorer displays the intended employees and connected
    entities.
-   [ ] Display deduplication does not mutate graph data or
    recommendation calculations.

## Limitations and production considerations

This is a POC, not a production certification. Before using it for live
business decisions, consider:

1.  **Score validation:** Backtest recommendations against historical
    outcomes. If scores are intended to represent probabilities,
    calibrate them and measure calibration quality.
2.  **Weight tuning:** The 50% / 30% / 20% weights are configured
    heuristics and should be reviewed with business stakeholders.
3.  **Data quality:** Normalize entity identifiers and domain names, and
    add uniqueness constraints where appropriate.
4.  **Cold-start correctness:** Distinguish missing evidence from
    evidence with zero wins.
5.  **Domain relevance:** Semantic similarity should be reviewed against
    business meaning; similar text does not always mean interchangeable
    expertise.
6.  **Transactions:** Create an opportunity and its related
    relationships atomically to avoid partial writes.
7.  **Identifier generation:** Avoid race-prone ID generation when
    multiple users create records concurrently.
8.  **Assignment workflow:** Provide an explicit assignment action and
    verify that ownership is persisted.
9.  **Security:** Add authentication, authorization, least-privilege
    database access, secure secret storage and HTTPS before deployment.
10. **Observability:** Add automated tests, structured logs, API metrics
    and error monitoring.
11. **Graph scalability:** Add filters and focused subgraph views as the
    number of entities grows.

## Troubleshooting

### Streamlit cannot reach FastAPI

-   Confirm FastAPI is running.
-   Check `API_BASE_URL` in `.env`.
-   Open `http://localhost:8000/docs` to confirm the API is reachable.
-   Check terminal output for backend errors.

### Neo4j connection fails

-   Confirm Neo4j is running.
-   Check `NEO4J_URI`, username, password and database.
-   Verify that Bolt port `7687` is available in your configuration.

### A new domain has no similar domains

-   Confirm the Domain node exists.
-   Run the domain embedding/similarity build or update workflow.
-   Check the configured similarity threshold.
-   An empty result may be valid if no domain passes the threshold.

### An opportunity exists but has no salesperson owner

-   Check whether the creation request included a valid `employee_id`.
-   Verify that the backend created `Employee -[:OWNS]-> Opportunity`.
-   Remember that recommendation and assignment are separate operations.

### Graph Explorer does not show all employees

-   Check whether the graph API returns only the selected employee's
    neighborhood.
-   Review traversal depth and node/relationship filters.
-   An all-salespeople graph may require a backend query that fetches
    all employees and their relevant connected entities.

## License and usage

Add the license that applies to your repository before distributing or
reusing this project. Do not include real credentials, customer data, or
other sensitive information in public commits.

## Acknowledgements

Built as a CRM Analytics Proof of Concept exploring graph-based
relationship modeling, semantic domain similarity, evidence-backed
salesperson ranking, and interactive CRM graph visualization.
