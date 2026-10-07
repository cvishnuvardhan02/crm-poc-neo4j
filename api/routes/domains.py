from fastapi import APIRouter, HTTPException

from services.domain_similarity import (
    domain_similarity_engine
)


router = APIRouter(
    prefix="/domains",
    tags=["Domain Similarity"]
)


# ============================================================
# GET DOMAINS
# ============================================================

@router.get("")
def get_domains():

    try:

        domains = (
            domain_similarity_engine
            .get_domains()
        )

        return {
            "count": len(domains),
            "domains": domains
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to retrieve domains",
                "error": str(exc)
            }
        )


# ============================================================
# BUILD ALL EMBEDDINGS
# ============================================================

@router.post("/embeddings/build")
def build_embeddings():

    try:

        return (
            domain_similarity_engine
            .build_embeddings()
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to build embeddings",
                "error": str(exc)
            }
        )


# ============================================================
# BUILD COMPLETE SIMILARITY GRAPH
# ============================================================

@router.post("/similarity/build")
def build_similarity():

    try:

        return (
            domain_similarity_engine
            .build_similarity_graph(
                clear_existing=True
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to build domain similarity",
                "error": str(exc)
            }
        )


# ============================================================
# UPDATE ONE DOMAIN
# ============================================================

@router.post("/{domain_name}/similarity")
def update_domain_similarity(
    domain_name: str
):

    try:

        return (
            domain_similarity_engine
            .update_domain(
                domain_name
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to update domain similarity",
                "error": str(exc)
            }
        )


# ============================================================
# GET SIMILAR DOMAINS
# ============================================================

@router.get("/{domain_name}/similar")
def get_similar_domains(
    domain_name: str,
    limit: int = 10
):

    try:

        results = (
            domain_similarity_engine
            .get_similar_domains(
                domain_name,
                limit
            )
        )

        return {
            "domain": domain_name,
            "count": len(results),
            "similar_domains": results
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Failed to retrieve similar domains",
                "error": str(exc)
            }
        )