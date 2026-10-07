from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from neo4j import GraphDatabase
import os


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"]
)


# ============================================================
# NEO4J
# ============================================================

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


# ============================================================
# REQUEST MODEL
# ============================================================

class OpportunityCreate(BaseModel):

    name: str

    customer_name: str

    domain: str

    value: float

    employee_id: Optional[str] = None


# ============================================================
# CREATE OPPORTUNITY
# ============================================================

@router.post("")
def create_opportunity(
    request: OpportunityCreate
):

    try:

        with driver.session(
            database=NEO4J_DATABASE
        ) as session:

            # ------------------------------------------------
            # Generate opportunity ID
            # ------------------------------------------------

            id_result = session.run(
                """
                MATCH (o:Opportunity)

                WITH
                    collect(
                        toInteger(
                            replace(o.id, 'O', '')
                        )
                    ) AS ids

                RETURN
                    'O' +
                    toString(
                        CASE
                            WHEN size(ids) = 0
                            THEN 1
                            ELSE reduce(
                                maxId = 0,
                                x IN ids |
                                CASE
                                    WHEN x > maxId
                                    THEN x
                                    ELSE maxId
                                END
                            ) + 1
                        END
                    ) AS opportunity_id
                """
            )

            opportunity_id = id_result.single()[
                "opportunity_id"
            ]


            # ------------------------------------------------
            # MERGE CUSTOMER
            # ------------------------------------------------

            customer_result = session.run(
                """
                MERGE (c:Customer {
                    name: $customer_name
                })

                RETURN
                    elementId(c) AS id,
                    c.name AS name
                """,

                customer_name=request.customer_name
            )

            customer_result.single()


            # ------------------------------------------------
            # MERGE DOMAIN
            # ------------------------------------------------

            domain_result = session.run(
                """
                MERGE (d:Domain {
                    name: $domain
                })

                RETURN
                    elementId(d) AS id,
                    d.name AS name
                """,

                domain=request.domain.strip()
            )

            domain_result.single()


            # ------------------------------------------------
            # CREATE OPPORTUNITY
            # ------------------------------------------------

            opportunity_result = session.run(
                """
                MATCH (d:Domain {
                    name: $domain
                })

                MATCH (c:Customer {
                    name: $customer_name
                })

                CREATE (o:Opportunity {
                    id: $opportunity_id,
                    name: $name,
                    value: $value,
                    stage: 'Open',
                    outcome: null
                })

                CREATE (o)-[:TARGETS]->(d)

                CREATE (o)-[:FOR_CUSTOMER]->(c)

                RETURN
                    o.id AS opportunity_id,
                    o.name AS name,
                    o.value AS value,
                    o.stage AS stage,
                    d.name AS domain,
                    c.name AS customer
                """,

                opportunity_id=opportunity_id,
                name=request.name.strip(),
                value=request.value,
                domain=request.domain.strip(),
                customer_name=request.customer_name.strip()
            )

            opportunity = (
                opportunity_result.single()
            )


            # ------------------------------------------------
            # ASSIGN SALESPERSON
            # ------------------------------------------------

            if request.employee_id:

                session.run(
                    """
                    MATCH
                        (e:Employee {
                            id: $employee_id
                        })

                    MATCH
                        (o:Opportunity {
                            id: $opportunity_id
                        })

                    MERGE
                        (e)-[:OWNS]->(o)
                    """,

                    employee_id=request.employee_id,
                    opportunity_id=opportunity_id
                )


            # ------------------------------------------------
            # RESPONSE
            # ------------------------------------------------

            return {
                "success": True,

                "message":
                    "Opportunity created successfully",

                "opportunity":
                    dict(opportunity)
            }


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to create opportunity",

                "error":
                    str(exc)
            }
        )

from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from neo4j import GraphDatabase

import os


# ============================================================
# CREATE OPPORTUNITY MODEL
# ============================================================

class OpportunityCreate(BaseModel):

    name: str

    customer_name: str

    domain: str

    value: float

    employee_id: Optional[str] = None


# ============================================================
# CREATE OPPORTUNITY
# ============================================================

@router.post("")
def create_opportunity(
    opportunity: OpportunityCreate
):

    try:

        uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687"
        )

        user = os.getenv(
            "NEO4J_USER",
            "neo4j"
        )

        password = os.getenv(
            "NEO4J_PASSWORD",
            "password"
        )

        database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j"
        )

        driver = GraphDatabase.driver(
            uri,
            auth=(user, password)
        )

        with driver.session(
            database=database
        ) as session:

            # ------------------------------------------------
            # GENERATE NEXT OPPORTUNITY ID
            # ------------------------------------------------

            id_query = """
            MATCH (o:Opportunity)
            WHERE o.id IS NOT NULL
            RETURN
                coalesce(
                    max(
                        toInteger(
                            replace(o.id, 'O', '')
                        )
                    ),
                    0
                ) + 1 AS next_id
            """

            record = session.run(
                id_query
            ).single()

            next_id = record["next_id"]

            opportunity_id = f"O{next_id:03d}"

            # ------------------------------------------------
            # CREATE GRAPH STRUCTURE
            # ------------------------------------------------

            query = """
            MERGE (c:Customer {
                name: $customer_name
            })

            MERGE (d:Domain {
                name: $domain
            })

            CREATE (o:Opportunity {
                id: $opportunity_id,
                name: $name,
                value: $value,
                stage: 'Open',
                outcome: null
            })

            CREATE (o)-[:FOR_CUSTOMER]->(c)

            CREATE (o)-[:TARGETS]->(d)

            WITH o, c, d

            OPTIONAL MATCH (
                e:Employee {
                    id: $employee_id
                }
            )

            FOREACH (
                employee IN CASE
                    WHEN e IS NOT NULL
                    THEN [e]
                    ELSE []
                END |
                CREATE (employee)-[:OWNS]->(o)
            )

            RETURN
                o.id AS opportunity_id,
                o.name AS opportunity_name,
                o.value AS opportunity_value,
                o.stage AS stage,
                c.name AS customer_name,
                d.name AS domain
            """

            result = session.run(
                query,
                opportunity_id=opportunity_id,
                name=opportunity.name,
                value=opportunity.value,
                customer_name=opportunity.customer_name,
                domain=opportunity.domain,
                employee_id=opportunity.employee_id
            ).single()

        driver.close()

        if result is None:

            raise HTTPException(
                status_code=500,
                detail="Failed to create opportunity."
            )

        return {
            "success": True,
            "message": "Opportunity created successfully.",
            "opportunity": dict(result)
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to create opportunity.",
                "error": str(exc)
            }
        )