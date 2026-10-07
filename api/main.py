import os
import math
from datetime import date, datetime, time
from decimal import Decimal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from neo4j import GraphDatabase

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# IMPORTANT:
# Your Neo4j database is "neo4j", not "crm"
NEO4J_DATABASE = "neo4j"

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000"
)


# ============================================================
# NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="CRM Analytics Engine",
    description="Neo4j-powered CRM Analytics POC",
    version="1.0.0"
)


# ============================================================
# JSON SAFETY
# ============================================================

def make_json_safe(value):
    """
    Recursively convert Neo4j/Python values into JSON-safe values.

    Important:
    Python float('nan') and infinity are not valid JSON values.
    They are converted to None.
    """

    if value is None:
        return None

    # Boolean must come before int because bool is a subclass of int
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if isinstance(value, str):
        return value

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Decimal):
        numeric_value = float(value)

        if math.isnan(numeric_value) or math.isinf(numeric_value):
            return None

        return numeric_value

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    try:
        return str(value)
    except Exception:
        return None


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Verify Neo4j connection when FastAPI starts.
    """

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("RETURN 1 AS value")
            result.single()

        print("=" * 70)
        print("CRM ANALYTICS ENGINE")
        print("=" * 70)
        print("Neo4j connection: SUCCESS")
        print(f"Database: {NEO4J_DATABASE}")
        print("=" * 70)

    except Exception as exc:
        print("=" * 70)
        print("Neo4j connection: FAILED")
        print(str(exc))
        print("=" * 70)


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
def shutdown_event():
    driver.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": "CRM Analytics Engine",
        "status": "running",
        "database": NEO4J_DATABASE,
        "api": API_BASE_URL
    }


# ============================================================
# DEBUG NEO4J
# ============================================================

@app.get("/debug/neo4j")
def debug_neo4j():

    return {
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_database": NEO4J_DATABASE
    }


# ============================================================
# NEO4J HEALTH CHECK
# ============================================================

@app.get("/health/neo4j")
def neo4j_health():

    try:

        with driver.session(
            database=NEO4J_DATABASE
        ) as session:

            result = session.run(
                "RETURN 1 AS value"
            )

            result.single()

        return {
            "status": "healthy",
            "database": NEO4J_DATABASE,
            "neo4j": True
        }

    except Exception as exc:

        return {
            "status": "unhealthy",
            "database": NEO4J_DATABASE,
            "neo4j": False,
            "error": str(exc)
        }


# ============================================================
# GRAPH EXPLORER
# ============================================================

@app.get("/graph")
def get_graph(
    entity_type: str = Query(
        ...,
        description="Neo4j label, for example Employee"
    ),
    entity_name: str = Query(
        ...,
        description="Entity name, for example John"
    ),
    depth: int = Query(
        2,
        ge=1,
        le=4,
        description="Graph traversal depth"
    )
):

    print()
    print("=" * 70)
    print("GRAPH REQUEST")
    print("=" * 70)
    print(f"Entity type: {entity_type}")
    print(f"Entity name: {entity_name}")
    print(f"Depth: {depth}")
    print(f"Database: {NEO4J_DATABASE}")
    print("=" * 70)

    # --------------------------------------------------------
    # FIND START ENTITY
    # --------------------------------------------------------

    find_entity_query = """
    MATCH (n)
    WHERE $entity_type IN labels(n)
      AND (
          n.name = $entity_name
          OR n.id = $entity_name
          OR n.employee_id = $entity_name
          OR n.customer_id = $entity_name
          OR n.opportunity_id = $entity_name
          OR n.domain_id = $entity_name
          OR n.product_id = $entity_name
      )

    RETURN
        elementId(n) AS id,
        labels(n) AS labels,
        properties(n) AS properties

    LIMIT 1
    """

    try:

        with driver.session(
            database=NEO4J_DATABASE
        ) as session:

            entity_result = session.run(
                find_entity_query,
                entity_type=entity_type,
                entity_name=entity_name
            )

            entity_record = entity_result.single()

            if entity_record is None:

                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "Entity not found",
                        "entity_type": entity_type,
                        "entity_name": entity_name
                    }
                )

            print(
                "ENTITY FOUND:",
                entity_record["properties"]
            )

            # ------------------------------------------------
            # FIND CONNECTED NODES
            # ------------------------------------------------

            nodes_query = f"""
            MATCH (start)
            WHERE $entity_type IN labels(start)
              AND (
                  start.name = $entity_name
                  OR start.id = $entity_name
                  OR start.employee_id = $entity_name
                  OR start.customer_id = $entity_name
                  OR start.opportunity_id = $entity_name
                  OR start.domain_id = $entity_name
                  OR start.product_id = $entity_name
              )

            MATCH p = (start)-[*1..{depth}]-(connected)

            UNWIND nodes(p) AS n

            RETURN DISTINCT
                elementId(n) AS id,
                labels(n) AS labels,
                properties(n) AS properties
            """

            nodes_result = session.run(
                nodes_query,
                entity_type=entity_type,
                entity_name=entity_name
            )

            nodes = []

            for record in nodes_result:

                node = {
                    "id": record["id"],
                    "labels": record["labels"],
                    "properties": record["properties"]
                }

                nodes.append(
                    make_json_safe(node)
                )

            # ------------------------------------------------
            # FIND RELATIONSHIPS
            # ------------------------------------------------

            relationships_query = f"""
            MATCH (start)
            WHERE $entity_type IN labels(start)
              AND (
                  start.name = $entity_name
                  OR start.id = $entity_name
                  OR start.employee_id = $entity_name
                  OR start.customer_id = $entity_name
                  OR start.opportunity_id = $entity_name
                  OR start.domain_id = $entity_name
                  OR start.product_id = $entity_name
              )

            MATCH p = (start)-[*1..{depth}]-(connected)

            UNWIND relationships(p) AS r

            RETURN DISTINCT
                elementId(r) AS id,
                elementId(startNode(r)) AS source,
                elementId(endNode(r)) AS target,
                type(r) AS label
            """

            relationships_result = session.run(
                relationships_query,
                entity_type=entity_type,
                entity_name=entity_name
            )

            relationships = []

            for record in relationships_result:

                relationship = {
                    "id": record["id"],
                    "source": record["source"],
                    "target": record["target"],
                    "label": record["label"]
                }

                relationships.append(
                    make_json_safe(relationship)
                )

    except HTTPException:
        raise

    except Exception as exc:

        print()
        print("=" * 70)
        print("GRAPH ERROR")
        print("=" * 70)
        print(str(exc))
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve graph",
                "error": str(exc)
            }
        )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    response = {
        "entity": {
            "type": entity_type,
            "name": entity_name
        },
        "nodes": nodes,
        "relationships": relationships,
        "node_count": len(nodes),
        "relationship_count": len(relationships)
    }

    # VERY IMPORTANT
    # Sanitize the entire response again before FastAPI
    # attempts JSON serialization.
    response = make_json_safe(response)

    print()
    print("=" * 70)
    print("GRAPH SUCCESS")
    print(f"Nodes: {len(nodes)}")
    print(f"Relationships: {len(relationships)}")
    print("=" * 70)

    return response


# ============================================================
# IMPORT EXISTING ROUTERS
# ============================================================

try:

    from api.routes.employees import (
        router as employees_router
    )

    app.include_router(
        employees_router
    )

    print("Employees router loaded.")

except Exception as exc:

    print(
        f"Employees router not loaded: {exc}"
    )


try:

    from api.routes.opportunities import (
        router as opportunities_router
    )

    app.include_router(
        opportunities_router
    )

    print("Opportunities router loaded.")

except Exception as exc:

    print(
        f"Opportunities router not loaded: {exc}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

try:
    from api.routes.opportunity_create import router as opportunity_create_router

    app.include_router(
        opportunity_create_router
    )

    print("Opportunity creation router loaded.")

except Exception as exc:

    print(
        f"Opportunity creation router not loaded: {exc}"
    )

try:

    from api.routes.domains import (
        router as domains_router
    )

    app.include_router(
        domains_router
    )

    print(
        "Domains router loaded."
    )

except Exception as exc:

    print(
        f"Domains router not loaded: {exc}"
    )


try:

    from api.routes.recommendations import (
        router as recommendations_router
    )

    app.include_router(
        recommendations_router
    )

    print(
        "Recommendations router loaded."
    )

except Exception as exc:

    print(
        f"Recommendations router not loaded: {exc}"
    )


try:

    from api.routes.domains import (
        router as domains_router
    )

    app.include_router(
        domains_router
    )

    print(
        "Domains router loaded."
    )

except Exception as exc:

    print(
        f"Domains router not loaded: {exc}"
    )

