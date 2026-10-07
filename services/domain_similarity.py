import os
from typing import Dict, List, Any

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class DomainSimilarityEngine:

    def __init__(self):

        self.neo4j_uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687"
        )

        self.neo4j_user = os.getenv(
            "NEO4J_USER",
            "neo4j"
        )

        self.neo4j_password = os.getenv(
            "NEO4J_PASSWORD",
            "password"
        )

        self.neo4j_database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j"
        )

        self.model_name = os.getenv(
            "EMBEDDING_MODEL",
            "all-MiniLM-L6-v2"
        )

        self.similarity_threshold = float(
            os.getenv(
                "DOMAIN_SIMILARITY_THRESHOLD",
                "0.55"
            )
        )

        self.model = None

        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(
                self.neo4j_user,
                self.neo4j_password
            )
        )

    # ========================================================
    # LOAD MODEL LAZILY
    # ========================================================

    def _get_model(self):

        if self.model is None:

            print(
                f"Loading embedding model: "
                f"{self.model_name}"
            )

            self.model = SentenceTransformer(
                self.model_name
            )

            print(
                "Embedding model loaded."
            )

        return self.model

    # ========================================================
    # GET DOMAINS
    # ========================================================

    def get_domains(self) -> List[str]:

        query = """
        MATCH (d:Domain)
        WHERE d.name IS NOT NULL
        RETURN DISTINCT d.name AS name
        ORDER BY d.name
        """

        with self.driver.session(
            database=self.neo4j_database
        ) as session:

            result = session.run(query)

            return [
                record["name"]
                for record in result
            ]

    # ========================================================
    # EMBEDDING
    # ========================================================

    def generate_embedding(
        self,
        domain_name: str
    ) -> List[float]:

        model = self._get_model()

        # Keep the semantic representation deterministic.
        text = (
            f"Business technology domain: "
            f"{domain_name}"
        )

        vector = model.encode(
            text,
            normalize_embeddings=True
        )

        return [
            float(value)
            for value in vector
        ]

    # ========================================================
    # STORE DOMAIN EMBEDDING
    # ========================================================

    def store_domain_embedding(
        self,
        domain_name: str,
        embedding: List[float]
    ):

        query = """
        MATCH (d:Domain {name: $domain_name})
        SET d.embedding = $embedding
        RETURN d.name AS name
        """

        with self.driver.session(
            database=self.neo4j_database
        ) as session:

            record = session.run(
                query,
                domain_name=domain_name,
                embedding=embedding
            ).single()

            if record is None:

                raise ValueError(
                    f"Domain not found: "
                    f"{domain_name}"
                )

            return record["name"]

    # ========================================================
    # CREATE SIMILARITY RELATIONSHIP
    # ========================================================

    def create_similarity_relationship(
        self,
        source_domain: str,
        target_domain: str,
        score: float
    ):

        query = """
        MATCH (source:Domain {
            name: $source_domain
        })

        MATCH (target:Domain {
            name: $target_domain
        })

        MERGE (
            source
        )-[r:SIMILAR_TO]->(
            target
        )

        SET
            r.score = $score,
            r.method = 'semantic_embedding',
            r.model = $model

        RETURN
            source.name AS source,
            target.name AS target,
            r.score AS score
        """

        with self.driver.session(
            database=self.neo4j_database
        ) as session:

            record = session.run(
                query,
                source_domain=source_domain,
                target_domain=target_domain,
                score=float(score),
                model=self.model_name
            ).single()

            return dict(record)

    # ========================================================
    # REMOVE OLD SIMILARITY RELATIONSHIPS
    # ========================================================

    def clear_similarity_relationships(self):

        query = """
        MATCH ()-[r:SIMILAR_TO]->()
        DELETE r
        """

        with self.driver.session(
            database=self.neo4j_database
        ) as session:

            result = session.run(query)

            summary = result.consume()

            return summary.counters.relationships_deleted

    # ========================================================
    # BUILD ALL DOMAIN EMBEDDINGS
    # ========================================================

    def build_embeddings(self):

        domains = self.get_domains()

        if not domains:

            return {
                "domains": 0,
                "message": "No domains found."
            }

        results = []

        for domain in domains:

            embedding = self.generate_embedding(
                domain
            )

            self.store_domain_embedding(
                domain,
                embedding
            )

            results.append({
                "domain": domain,
                "embedding_dimensions":
                    len(embedding)
            })

        return {
            "domains": len(domains),
            "embedding_model":
                self.model_name,
            "results": results
        }

    # ========================================================
    # BUILD SIMILARITY GRAPH
    # ========================================================

    def build_similarity_graph(
        self,
        clear_existing=True
    ):

        domains = self.get_domains()

        if len(domains) < 2:

            return {
                "domains": len(domains),
                "relationships_created": 0,
                "message":
                    "At least two domains are required."
            }

        # ----------------------------------------------------
        # Generate embeddings
        # ----------------------------------------------------

        embeddings = []

        for domain in domains:

            embedding = self.generate_embedding(
                domain
            )

            self.store_domain_embedding(
                domain,
                embedding
            )

            embeddings.append(
                embedding
            )

        # ----------------------------------------------------
        # Clear old relationships
        # ----------------------------------------------------

        deleted = 0

        if clear_existing:

            deleted = (
                self.clear_similarity_relationships()
            )

        # ----------------------------------------------------
        # Calculate similarity matrix
        # ----------------------------------------------------

        similarity_matrix = cosine_similarity(
            embeddings
        )

        relationships = []

        # ----------------------------------------------------
        # Create directed relationships
        # ----------------------------------------------------

        for i, source_domain in enumerate(
            domains
        ):

            for j, target_domain in enumerate(
                domains
            ):

                # Don't connect a domain to itself.
                if i == j:
                    continue

                score = float(
                    similarity_matrix[i][j]
                )

                if (
                    score
                    < self.similarity_threshold
                ):
                    continue

                relationship = (
                    self.create_similarity_relationship(
                        source_domain,
                        target_domain,
                        score
                    )
                )

                relationships.append(
                    relationship
                )

        return {
            "domains": len(domains),
            "relationships_created":
                len(relationships),
            "relationships_deleted":
                deleted,
            "threshold":
                self.similarity_threshold,
            "embedding_model":
                self.model_name,
            "relationships":
                relationships
        }

    # ========================================================
    # UPDATE ONE NEW DOMAIN
    # ========================================================

    def update_domain(
        self,
        domain_name: str
    ) -> Dict[str, Any]:

        domains = self.get_domains()

        if domain_name not in domains:

            raise ValueError(
                f"Domain '{domain_name}' "
                f"does not exist."
            )

        # ----------------------------------------------------
        # Generate embedding for new domain
        # ----------------------------------------------------

        new_embedding = (
            self.generate_embedding(
                domain_name
            )
        )

        self.store_domain_embedding(
            domain_name,
            new_embedding
        )

        # ----------------------------------------------------
        # Get existing domains
        # ----------------------------------------------------

        other_domains = [
            domain
            for domain in domains
            if domain != domain_name
        ]

        if not other_domains:

            return {
                "domain": domain_name,
                "relationships_created": 0,
                "relationships": []
            }

        # ----------------------------------------------------
        # Generate embeddings
        # ----------------------------------------------------

        other_embeddings = []

        for domain in other_domains:

            embedding = (
                self.generate_embedding(
                    domain
                )
            )

            self.store_domain_embedding(
                domain,
                embedding
            )

            other_embeddings.append(
                embedding
            )

        # ----------------------------------------------------
        # Calculate similarities
        # ----------------------------------------------------

        scores = cosine_similarity(
            [new_embedding],
            other_embeddings
        )[0]

        relationships = []

        for domain, score in zip(
            other_domains,
            scores
        ):

            score = float(score)

            if (
                score
                < self.similarity_threshold
            ):
                continue

            # New → Existing
            relationships.append(
                self.create_similarity_relationship(
                    domain_name,
                    domain,
                    score
                )
            )

            # Existing → New
            relationships.append(
                self.create_similarity_relationship(
                    domain,
                    domain_name,
                    score
                )
            )

        return {
            "domain": domain_name,
            "relationships_created":
                len(relationships),
            "threshold":
                self.similarity_threshold,
            "embedding_model":
                self.model_name,
            "relationships":
                relationships
        }

    # ========================================================
    # GET RECOMMENDATIONS FOR DOMAIN
    # ========================================================

    def get_similar_domains(
        self,
        domain_name: str,
        limit: int = 10
    ):

        query = """
        MATCH (
            source:Domain {
                name: $domain_name
            }
        )
        -[r:SIMILAR_TO]->
        (target:Domain)

        RETURN
            source.name AS source_domain,
            target.name AS target_domain,
            r.score AS score,
            r.method AS method,
            r.model AS model

        ORDER BY r.score DESC

        LIMIT $limit
        """

        with self.driver.session(
            database=self.neo4j_database
        ) as session:

            result = session.run(
                query,
                domain_name=domain_name,
                limit=limit
            )

            return [
                dict(record)
                for record in result
            ]

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.driver.close()


# Singleton instance
domain_similarity_engine = (
    DomainSimilarityEngine()
)