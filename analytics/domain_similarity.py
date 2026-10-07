import math
import os
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def _domain_vectors(driver):
    query = '''
    MATCH (d:Domain)<-[:TARGETS]-(o:Opportunity)
    RETURN d.name AS domain, collect(o.id) AS opportunities
    '''
    with driver.session() as session:
        return {r["domain"]: set(r["opportunities"]) for r in session.run(query)}


def jaccard(a, b):
    union = a | b
    return len(a & b) / len(union) if union else 0


def get_domain_similarity():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        vectors = _domain_vectors(driver)
        domains = sorted(vectors)
        result = []
        for i, d1 in enumerate(domains):
            for d2 in domains[i + 1:]:
                score = jaccard(vectors[d1], vectors[d2])
                result.append({
                    "domain_1": d1,
                    "domain_2": d2,
                    "similarity": round(score, 4)
                })
        return sorted(result, key=lambda x: x["similarity"], reverse=True)
    finally:
        driver.close()


def similar_domains(domain, top_n=5):
    pairs = get_domain_similarity()
    output = []
    for p in pairs:
        if p["domain_1"] == domain:
            output.append({"domain": p["domain_2"], "similarity": p["similarity"]})
        elif p["domain_2"] == domain:
            output.append({"domain": p["domain_1"], "similarity": p["similarity"]})
    return sorted(output, key=lambda x: x["similarity"], reverse=True)[:top_n]
