import os

from neo4j import GraphDatabase


class SalespersonRecommendationEngine:

    def __init__(self):

        self.uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687"
        )

        self.user = os.getenv(
            "NEO4J_USER",
            "neo4j"
        )

        self.password = os.getenv(
            "NEO4J_PASSWORD",
            "password"
        )

        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j"
        )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.user,
                self.password
            )
        )

    # ========================================================
    # GET OPPORTUNITY
    # ========================================================

    def get_opportunity(
        self,
        opportunity_id
    ):

        query = """
        MATCH (o:Opportunity {id: $opportunity_id})

        OPTIONAL MATCH
            (o)-[:TARGETS]->(d:Domain)

        OPTIONAL MATCH
            (o)-[:FOR_CUSTOMER]->(c:Customer)

        RETURN
            o.id AS opportunity_id,
            o.name AS opportunity_name,
            o.value AS opportunity_value,
            o.stage AS stage,
            o.outcome AS outcome,
            d.name AS domain,
            c.name AS customer
        """

        with self.driver.session(
            database=self.database
        ) as session:

            record = session.run(
                query,
                opportunity_id=opportunity_id
            ).single()

        if record is None:
            return None

        return dict(record)

    # ========================================================
    # GET ALL EMPLOYEES
    # ========================================================

    def get_employees(self):

        query = """
        MATCH (e:Employee)

        RETURN
            e.id AS employee_id,
            e.name AS employee_name

        ORDER BY e.name
        """

        with self.driver.session(
            database=self.database
        ) as session:

            return [
                dict(record)
                for record in session.run(query)
            ]

    # ========================================================
    # HISTORICAL PERFORMANCE
    #
    # IMPORTANT:
    # Win rate = Won / (Won + Lost)
    #
    # Open opportunities are NOT treated as losses.
    # ========================================================

    def get_employee_performance(
        self,
        employee_id
    ):

        query = """
        MATCH (e:Employee {id: $employee_id})
              -[:OWNS]->
              (o:Opportunity)

        WITH
            count(o) AS opportunities,

            sum(
                CASE
                    WHEN o.outcome = 'Won'
                    THEN 1
                    ELSE 0
                END
            ) AS wins,

            sum(
                CASE
                    WHEN o.outcome = 'Lost'
                    THEN 1
                    ELSE 0
                END
            ) AS losses,

            sum(
                CASE
                    WHEN o.outcome = 'Won'
                    THEN coalesce(o.value, 0)
                    ELSE 0
                END
            ) AS revenue_won

        RETURN
            opportunities,
            wins,
            losses,
            revenue_won,

            CASE
                WHEN (wins + losses) > 0
                THEN toFloat(wins) / (wins + losses)
                ELSE 0.0
            END AS win_rate
        """

        with self.driver.session(
            database=self.database
        ) as session:

            record = session.run(
                query,
                employee_id=employee_id
            ).single()

        if record is None:

            return {
                "opportunities": 0,
                "wins": 0,
                "losses": 0,
                "revenue_won": 0,
                "win_rate": 0.0
            }

        return dict(record)

    # ========================================================
    # EMPLOYEE DOMAIN SIMILARITY
    # ========================================================

    def get_domain_similarity(
        self,
        employee_id,
        target_domain
    ):

        query = """
        MATCH (e:Employee {id: $employee_id})
              -[:OWNS]->
              (o:Opportunity)
              -[:TARGETS]->
              (d:Domain)

        WHERE o.outcome = 'Won'

        OPTIONAL MATCH
            (target:Domain {name: $target_domain})
            -[s:SIMILAR_TO]-
            (d)

        WITH
            d,
            max(
                CASE
                    WHEN d.name = $target_domain
                    THEN 1.0
                    ELSE coalesce(s.score, 0.0)
                END
            ) AS similarity

        RETURN
            max(similarity) AS domain_similarity
        """

        with self.driver.session(
            database=self.database
        ) as session:

            record = session.run(
                query,
                employee_id=employee_id,
                target_domain=target_domain
            ).single()

        if (
            record is None
            or record["domain_similarity"] is None
        ):

            return 0.0

        return float(
            record["domain_similarity"]
        )

    # ========================================================
    # DOMAIN EVIDENCE
    # ========================================================

    def get_domain_evidence(
        self,
        employee_id,
        target_domain
    ):

        query = """
        MATCH (e:Employee {id: $employee_id})
              -[:OWNS]->
              (o:Opportunity)
              -[:TARGETS]->
              (d:Domain)

        WHERE o.outcome = 'Won'

        OPTIONAL MATCH
            (target:Domain {name: $target_domain})
            -[s:SIMILAR_TO]-
            (d)

        WITH
            o,
            d,
            max(
                CASE
                    WHEN d.name = $target_domain
                    THEN 1.0
                    ELSE coalesce(s.score, 0.0)
                END
            ) AS similarity

        RETURN
            o.name AS opportunity,
            d.name AS domain,
            o.outcome AS outcome,
            similarity

        ORDER BY similarity DESC

        LIMIT 10
        """

        with self.driver.session(
            database=self.database
        ) as session:

            return [
                dict(record)
                for record in session.run(
                    query,
                    employee_id=employee_id,
                    target_domain=target_domain
                )
            ]

    # ========================================================
    # PEER SUCCESS
    # ========================================================

    def get_peer_success(
        self,
        target_domain
    ):

        query = """
        MATCH (e:Employee)
              -[:OWNS]->
              (o:Opportunity)
              -[:TARGETS]->
              (d:Domain)

        WHERE o.outcome = 'Won'

        OPTIONAL MATCH
            (target:Domain {name: $target_domain})
            -[s:SIMILAR_TO]-
            (d)

        WITH
            d,
            max(
                CASE
                    WHEN d.name = $target_domain
                    THEN 1.0
                    ELSE coalesce(s.score, 0.0)
                END
            ) AS similarity

        WHERE similarity > 0

        RETURN
            avg(similarity) AS peer_success
        """

        with self.driver.session(
            database=self.database
        ) as session:

            record = session.run(
                query,
                target_domain=target_domain
            ).single()

        if (
            record is None
            or record["peer_success"] is None
        ):

            return 0.0

        return float(
            record["peer_success"]
        )

    # ========================================================
    # PEER EVIDENCE
    # ========================================================

    def get_peer_evidence(
        self,
        target_domain
    ):

        query = """
        MATCH (e:Employee)
              -[:OWNS]->
              (o:Opportunity)
              -[:TARGETS]->
              (d:Domain)

        WHERE o.outcome = 'Won'

        OPTIONAL MATCH
            (target:Domain {name: $target_domain})
            -[s:SIMILAR_TO]-
            (d)

        WITH
            e,
            o,
            d,
            max(
                CASE
                    WHEN d.name = $target_domain
                    THEN 1.0
                    ELSE coalesce(s.score, 0.0)
                END
            ) AS similarity

        WHERE similarity > 0

        RETURN
            e.name AS employee,
            o.name AS opportunity,
            d.name AS domain,
            o.outcome AS outcome,
            similarity

        ORDER BY similarity DESC

        LIMIT 20
        """

        with self.driver.session(
            database=self.database
        ) as session:

            return [
                dict(record)
                for record in session.run(
                    query,
                    target_domain=target_domain
                )
            ]

    # ========================================================
    # RANK SALESPERSONS
    # ========================================================

    def rank_salespeople(
        self,
        opportunity_id,
        limit=10
    ):

        # ----------------------------------------------------
        # Get opportunity
        # ----------------------------------------------------

        opportunity = self.get_opportunity(
            opportunity_id
        )

        if opportunity is None:

            raise ValueError(
                f"Opportunity '{opportunity_id}' "
                f"not found."
            )

        target_domain = (
            opportunity.get("domain")
        )

        if not target_domain:

            raise ValueError(
                "Opportunity does not have "
                "a target domain."
            )

        # ----------------------------------------------------
        # Get employees
        # ----------------------------------------------------

        employees = self.get_employees()

        # ----------------------------------------------------
        # Calculate team-wide peer success
        # ----------------------------------------------------

        peer_success = self.get_peer_success(
            target_domain
        )

        # ----------------------------------------------------
        # Get peer evidence once
        # ----------------------------------------------------

        peer_evidence = self.get_peer_evidence(
            target_domain
        )

        recommendations = []

        # ====================================================
        # SCORE EVERY SALESPERSON
        # ====================================================

        for employee in employees:

            employee_id = (
                employee["employee_id"]
            )

            employee_name = (
                employee["employee_name"]
            )

            # ------------------------------------------------
            # Historical performance
            # ------------------------------------------------

            performance = (
                self.get_employee_performance(
                    employee_id
                )
            )

            historical_performance = float(
                performance.get(
                    "win_rate",
                    0.0
                ) or 0.0
            )

            # ------------------------------------------------
            # Domain similarity
            # ------------------------------------------------

            domain_similarity = (
                self.get_domain_similarity(
                    employee_id,
                    target_domain
                )
            )

            # ------------------------------------------------
            # Final weighted score
            # ------------------------------------------------

            final_score = (
                0.50 * domain_similarity
                +
                0.30 * peer_success
                +
                0.20 * historical_performance
            )

            # ------------------------------------------------
            # Explainability
            # ------------------------------------------------

            reasons = []

            if domain_similarity >= 0.80:

                reasons.append(
                    "Strong historical success "
                    "in the target or closely related domains."
                )

            elif domain_similarity >= 0.55:

                reasons.append(
                    "Relevant experience in domains "
                    "similar to the opportunity domain."
                )

            elif domain_similarity > 0:

                reasons.append(
                    "Some historical experience "
                    "in related domains."
                )

            else:

                reasons.append(
                    "No strong historical domain match "
                    "was found."
                )

            if peer_success >= 0.70:

                reasons.append(
                    "The wider sales team has strong "
                    "success in this domain or related domains."
                )

            elif peer_success >= 0.40:

                reasons.append(
                    "The wider sales team has moderate "
                    "success in this domain."
                )

            if historical_performance >= 0.70:

                reasons.append(
                    "Strong overall historical "
                    "conversion rate."
                )

            elif historical_performance >= 0.50:

                reasons.append(
                    "Consistent historical "
                    "sales performance."
                )

            # ------------------------------------------------
            # Recommendation object
            # ------------------------------------------------

            recommendations.append(
                {
                    "employee_id":
                        employee_id,

                    "employee_name":
                        employee_name,

                    "target_domain":
                        target_domain,

                    "score":
                        round(
                            final_score,
                            4
                        ),

                    "probability_percent":
                        round(
                            final_score * 100,
                            1
                        ),

                    "domain_similarity":
                        round(
                            domain_similarity,
                            4
                        ),

                    "peer_success":
                        round(
                            peer_success,
                            4
                        ),

                    "historical_performance":
                        round(
                            historical_performance,
                            4
                        ),

                    "total_opportunities":
                        performance.get(
                            "opportunities",
                            0
                        ),

                    "wins":
                        performance.get(
                            "wins",
                            0
                        ),

                    "losses":
                        performance.get(
                            "losses",
                            0
                        ),

                    "revenue_won":
                        performance.get(
                            "revenue_won",
                            0
                        ),

                    "reasons":
                        reasons,

                    "domain_evidence":
                        self.get_domain_evidence(
                            employee_id,
                            target_domain
                        ),

                    "peer_evidence":
                        peer_evidence
                }
            )

        # ====================================================
        # SORT BY SCORE
        # ====================================================

        recommendations.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # ====================================================
        # ADD RANK
        # ====================================================

        for index, recommendation in enumerate(
            recommendations[:limit],
            start=1
        ):

            recommendation["rank"] = index

        return recommendations[:limit]

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.driver.close()


# ============================================================
# SINGLETON
# ============================================================

salesperson_recommendation_engine = (
    SalespersonRecommendationEngine()
)