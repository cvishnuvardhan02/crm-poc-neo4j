import os
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_employee_domain_profiles():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        query = '''
        MATCH (e:Employee)-[:OWNS]->(o:Opportunity)-[:TARGETS]->(d:Domain)
        RETURN e.id AS employee_id, e.name AS employee,
               d.name AS domain,
               count(o) AS opportunities,
               sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) AS wins
        '''
        profiles = defaultdict(dict)
        with driver.session() as session:
            for r in session.run(query):
                profiles[r["employee_id"]][r["domain"]] = {
                    "opportunities": r["opportunities"],
                    "wins": r["wins"]
                }
        return profiles
    finally:
        driver.close()


def cosine_similarity(a, b):
    keys = set(a) | set(b)
    if not keys:
        return 0
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0


def get_employee_similarity():
    profiles = get_employee_domain_profiles()
    ids = list(profiles)
    output = []

    for i, e1 in enumerate(ids):
        for e2 in ids[i + 1:]:
            a = {d: x["wins"] for d, x in profiles[e1].items()}
            b = {d: x["wins"] for d, x in profiles[e2].items()}
            output.append({
                "employee_1": e1,
                "employee_2": e2,
                "similarity": round(cosine_similarity(a, b), 4)
            })

    return sorted(output, key=lambda x: x["similarity"], reverse=True)
