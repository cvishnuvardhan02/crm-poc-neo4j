import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_employee_metrics(employee_id=None):
    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    try:
        query = '''
        MATCH (e:Employee)-[:OWNS]->(o:Opportunity)
        WHERE $employee_id IS NULL OR e.id = $employee_id

        WITH
            e,
            collect(o) AS opps

        RETURN
            e.id AS employee_id,
            e.name AS employee,
            size(opps) AS opportunities,

            reduce(
                w = 0,
                x IN opps |
                w + CASE
                    WHEN x.outcome = 'Won'
                    THEN 1
                    ELSE 0
                END
            ) AS wins,

            reduce(
                l = 0,
                x IN opps |
                l + CASE
                    WHEN x.outcome = 'Lost'
                    THEN 1
                    ELSE 0
                END
            ) AS losses,

            reduce(
                op = 0,
                x IN opps |
                op + CASE
                    WHEN x.stage = 'Open'
                    THEN 1
                    ELSE 0
                END
            ) AS open,

            reduce(
                r = 0.0,
                x IN opps |
                r + CASE
                    WHEN x.outcome = 'Won'
                    THEN coalesce(x.value, 0)
                    ELSE 0
                END
            ) AS revenue_won
        ORDER BY employee
        '''

        with driver.session(
            database=DATABASE
        ) as session:

            rows = [
                r.data()
                for r in session.run(
                    query,
                    employee_id=employee_id
                )
            ]

        for row in rows:

            row["win_rate"] = round(
                row["wins"] / row["opportunities"],
                4
            ) if row["opportunities"] else 0

            row["average_deal_size"] = round(
                row["revenue_won"] / row["wins"],
                2
            ) if row["wins"] else 0

        return rows

    finally:
        driver.close()