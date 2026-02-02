"""
Loan Eligibility Agent - Main Application
FastAPI application for conversational loan pre-qualification.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.logging_config import setup_logging
from .api.routes import eligibility, conversation, webhook, health

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Loan Eligibility Agent API

    A conversational AI-powered loan pre-qualification system for financial services.

    ### Features

    - **Eligibility Assessment**: Comprehensive loan eligibility evaluation
    - **Conversational Interface**: Natural language interaction for loan pre-qualification
    - **Dialogflow Integration**: Webhook fulfillment for Dialogflow CX
    - **LLM-Powered Explanations**: Human-readable explanations of eligibility decisions

    ### Loan Types Supported

    - Personal Loans
    - Home Loans (Mortgages)
    - Auto Loans
    - Business Loans
    - Education Loans

    ### API Sections

    - `/api/v1/eligibility` - Direct eligibility assessment endpoints
    - `/api/v1/conversation` - Conversational interaction endpoints
    - `/api/v1/webhook` - Dialogflow CX webhook endpoints
    - `/health` - Service health checks
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Include routers
app.include_router(
    eligibility.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    conversation.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    webhook.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(health.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "health": "/health",
        "api_prefix": settings.API_V1_PREFIX
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
