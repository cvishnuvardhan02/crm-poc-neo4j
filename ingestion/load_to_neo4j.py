import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_data.csv"


class CRMLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def load(self, df: pd.DataFrame):
        query = '''
        UNWIND $rows AS row

        MERGE (c:Customer {id: row.customer_id})
        SET c.name = row.customer_name

        MERGE (i:Industry {name: row.industry})
        MERGE (e:Employee {id: row.employee_id})
        SET e.name = row.employee_name

        MERGE (d:Domain {name: row.domain})
        MERGE (p:Product {name: row.product})
        MERGE (s:Stage {name: row.stage})

        MERGE (o:Opportunity {id: row.opportunity_id})
        SET o.name = row.opportunity_name,
            o.value = toFloat(row.opportunity_value),
            o.outcome = row.outcome,
            o.interaction_count = toInteger(row.interaction_count),
            o.meeting_count = toInteger(row.meeting_count),
            o.days_in_stage = toInteger(row.days_in_stage),
            o.previous_customer_interactions = toInteger(row.previous_customer_interactions)

        MERGE (e)-[:OWNS]->(o)
        MERGE (o)-[:FOR_CUSTOMER]->(c)
        MERGE (o)-[:TARGETS]->(d)
        MERGE (c)-[:IN_INDUSTRY]->(i)
        MERGE (o)-[:FOR_PRODUCT]->(p)
        MERGE (o)-[:AT_STAGE]->(s)

        WITH e, c, row
        MERGE (interaction:Interaction {id: row.opportunity_id + '-INT'})
        SET interaction.count = toInteger(row.interaction_count),
            interaction.meetings = toInteger(row.meeting_count)
        MERGE (e)-[:PERFORMED]->(interaction)
        MERGE (interaction)-[:WITH]->(c)
        '''
        rows = df.to_dict("records")
        with self.driver.session() as session:
            session.run(query, rows=rows)

        print(f"Loaded {len(rows)} CRM records into Neo4j.")


if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)

    loader = CRMLoader()
    try:
        print("Clearing existing graph...")
        loader.clear_database()
        print("Loading CRM data...")
        loader.load(df)
    finally:
        loader.close()
