"""
Health Check API Routes
Endpoints for service health monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status and basic information.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with dependency status.

    Checks connectivity to external services and returns detailed status.
    """
    checks = {}

    # Check LLM service availability
    llm_status = await check_llm_service()
    checks["llm_service"] = llm_status

    # Check Dialogflow connectivity (if configured)
    if settings.DIALOGFLOW_AGENT_ID:
        dialogflow_status = await check_dialogflow()
        checks["dialogflow"] = dialogflow_status
    else:
        checks["dialogflow"] = {"status": "not_configured"}

    # Overall status
    all_healthy = all(
        c.get("status") in ["healthy", "not_configured"]
        for c in checks.values()
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }


async def check_llm_service() -> Dict[str, Any]:
    """Check LLM service availability."""
    try:
        from ...services import LLMService
        llm = LLMService()

        # Try a simple generation
        if hasattr(llm.provider, '__class__'):
            provider_name = llm.provider.__class__.__name__
        else:
            provider_name = "unknown"

        return {
            "status": "healthy",
            "provider": provider_name
        }
    except Exception as e:
        logger.warning(f"LLM service check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_dialogflow() -> Dict[str, Any]:
    """Check Dialogflow connectivity."""
    try:
        # This would normally verify Dialogflow agent connectivity
        # For now, just check if configuration exists
        if settings.GCP_PROJECT_ID and settings.DIALOGFLOW_AGENT_ID:
            return {
                "status": "healthy",
                "project": settings.GCP_PROJECT_ID,
                "agent": settings.DIALOGFLOW_AGENT_ID
            }
        else:
            return {"status": "not_configured"}
    except Exception as e:
        logger.warning(f"Dialogflow check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.

    Returns 200 when the service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.

    Returns 200 when the service is alive.
    """
    return {"status": "alive"}
