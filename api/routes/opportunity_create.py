import math
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import os

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunity Creation"]
)

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687"
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j"
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
    "password"
)

NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j"
)

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USER,
        NEO4J_PASSWORD
    )
)


class OpportunityCreate(BaseModel):

    opportunity_name: str = Field(
        ...,
        min_length=2
    )

    customer_name: str = Field(
        ...,
        min_length=2
    )

    domain: str = Field(
        ...,
        min_length=2
    )

    opportunity_value: float = Field(
        ...,
        gt=0
    )

    employee_id: str


def normalize_domain(value: str) -> str:

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.title()


@router.post("/create")
def create_opportunity(
    payload: OpportunityCreate
):

    domain_name = normalize_domain(
        payload.domain
    )

    try:

        with driver.session(
            database=NEO4J_DATABASE
        ) as session:

            # ------------------------------------------------
            # Verify salesperson
            # ------------------------------------------------

            employee = session.run(
                """
                MATCH (e:Employee)
                WHERE e.id = $employee_id
                RETURN e
                """,
                employee_id=payload.employee_id
            ).single()

            if employee is None:

                raise HTTPException(
                    status_code=404,
                    detail="Employee not found"
                )

            # ------------------------------------------------
            # Generate opportunity ID
            # ------------------------------------------------

            opportunity_id = session.run(
                """
                MATCH (o:Opportunity)
                RETURN
                    'O' +
                    toString(
                        coalesce(
                            max(
                                toInteger(
                                    substring(o.id, 1)
                                )
                            ),
                            0
                        ) + 1
                    ) AS id
                """
            ).single()["id"]

            # ------------------------------------------------
            # Create customer + domain + opportunity
            # ------------------------------------------------

            result = session.run(
                """
                MERGE (
                    c:Customer {
                        name: $customer_name
                    }
                )

                MERGE (
                    d:Domain {
                        name: $domain
                    }
                )

                CREATE (
                    o:Opportunity {
                        id: $opportunity_id,
                        name: $opportunity_name,
                        value: $value,
                        stage: 'Open',
                        outcome: null
                    }
                )

                WITH o, c, d

                MATCH (
                    e:Employee {
                        id: $employee_id
                    }
                )

                MERGE (
                    e
                )-[:OWNS]->(
                    o
                )

                MERGE (
                    o
                )-[:FOR_CUSTOMER]->(
                    c
                )

                MERGE (
                    o
                )-[:TARGETS]->(
                    d
                )

                RETURN
                    o.id AS opportunity_id,
                    o.name AS opportunity_name,
                    c.name AS customer_name,
                    d.name AS domain,
                    e.name AS employee_name,
                    o.value AS opportunity_value,
                    o.stage AS stage
                """,

                opportunity_id=opportunity_id,
                opportunity_name=payload.opportunity_name,
                customer_name=payload.customer_name,
                domain=domain_name,
                value=payload.opportunity_value,
                employee_id=payload.employee_id
            )

            record = result.single()

            return {
                "status": "created",
                "opportunity": dict(record)
            }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to create opportunity",
                "error": str(exc)
            }
        )