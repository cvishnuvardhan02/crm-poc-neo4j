import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from neo4j import GraphDatabase

from analytics.employee_metrics import get_employee_metrics
from recommendation.recommender import recommend_domains

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
def employees():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        query = "MATCH (e:Employee) RETURN e.id AS id, e.name AS name ORDER BY e.name"
        with driver.session() as session:
            return [r.data() for r in session.run(query)]
    finally:
        driver.close()


@router.get("/{employee_id}/performance")
def performance(employee_id: str):
    rows = get_employee_metrics(employee_id)
    if not rows:
        raise HTTPException(404, "Employee not found")
    return rows[0]


@router.get("/{employee_id}/recommendations")
def recommendations(employee_id: str):
    try:
        return {
            "employee_id": employee_id,
            "recommendations": recommend_domains(employee_id),
        }
    except Exception as exc:
        raise HTTPException(500, str(exc))
