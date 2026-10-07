from fastapi import APIRouter, HTTPException

from services.salesperson_recommendation import (
    salesperson_recommendation_engine
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get(
    "/opportunities/{opportunity_id}/salespeople"
)
def recommend_salespeople(
    opportunity_id: str,
    limit: int = 10
):

    try:

        salespeople = (
            salesperson_recommendation_engine
            .rank_salespeople(
                opportunity_id,
                limit
            )
        )

        return {
            "opportunity_id": opportunity_id,

            "recommendation_method":
                "Graph-based weighted scoring",

            "weights": {
                "domain_similarity": 0.50,
                "peer_success": 0.30,
                "historical_performance": 0.20
            },

            "salespeople": salespeople
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("RECOMMENDATION ERROR")
        print("=" * 70)
        print(str(exc))
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to rank salespeople",
                "error": str(exc)
            }
        )