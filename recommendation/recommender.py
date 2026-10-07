import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_driver():
    return GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )


def recommend_domains(employee_id, top_n=5):

    query = """
MATCH (e:Employee {id: $employee_id})
      -[:OWNS]->(o:Opportunity)
      -[:TARGETS]->(source:Domain)

WHERE o.outcome = "Won"

MATCH (source)-[s:SIMILAR_TO]->(recommended:Domain)

WHERE NOT EXISTS {
    MATCH (e)-[:OWNS]->(:Opportunity)-[:TARGETS]->(recommended)
}

WITH
    e,
    source,
    recommended,
    s.score AS domain_similarity

OPTIONAL MATCH (peer:Employee)-[:OWNS]->(peerOpp:Opportunity)
                -[:TARGETS]->(recommended)

WITH
    e,
    source,
    recommended,
    domain_similarity,

    CASE
        WHEN count(peerOpp) = 0 THEN 0.0
        ELSE
            toFloat(
                sum(
                    CASE
                        WHEN peerOpp.outcome = "Won"
                        THEN 1
                        ELSE 0
                    END
                )
            ) / count(peerOpp)
    END AS peer_success

MATCH (e)-[:OWNS]->(allOpp:Opportunity)

WITH
    e,
    source,
    recommended,
    domain_similarity,
    peer_success,

    toFloat(
        sum(
            CASE
                WHEN allOpp.outcome = "Won"
                THEN 1
                ELSE 0
            END
        )
    ) / count(allOpp) AS employee_performance

WITH
    e,
    source,
    recommended,
    domain_similarity,
    peer_success,
    employee_performance,

    (
        0.50 * domain_similarity +
        0.30 * peer_success +
        0.20 * employee_performance
    ) AS recommendation_score

// Keep only the best path to each recommended domain
WITH
    e,
    recommended,
    recommendation_score,
    domain_similarity,
    peer_success,
    employee_performance,
    source

ORDER BY recommendation_score DESC

WITH
    e,
    recommended,
    collect({
        score: recommendation_score,
        similarity: domain_similarity,
        peer_success: peer_success,
        performance: employee_performance,
        source: source.name
    })[0] AS best

RETURN
    e.id AS employee_id,
    e.name AS employee,
    recommended.name AS recommended_domain,

    round(best.score * 100, 2)
        AS recommendation_score_percent,

    round(best.similarity * 100, 2)
        AS domain_similarity_percent,

    round(best.peer_success * 100, 2)
        AS peer_success_percent,

    round(best.performance * 100, 2)
        AS employee_performance_percent,

    best.source AS source_domain

ORDER BY recommendation_score_percent DESC
LIMIT $top_n
"""

    driver = get_driver()

    try:
        with driver.session(database=DATABASE) as session:

            results = session.run(
                query,
                employee_id=employee_id,
                top_n=top_n
            )

            recommendations = []

            for record in results:

                recommendations.append({
                    "employee_id": record["employee_id"],
                    "employee": record["employee"],
                    "domain": record["recommended_domain"],
                    "score": record["recommendation_score_percent"],
                    "domain_similarity": record[
                        "domain_similarity_percent"
                    ],
                    "peer_success": record[
                        "peer_success_percent"
                    ],
                    "employee_performance": record[
                        "employee_performance_percent"
                    ],
                    "source_domain": record["source_domain"]
                })

            return recommendations

    finally:
        driver.close()