"""
Eligibility API Routes
REST endpoints for loan eligibility assessment.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ...models import (
    LoanType,
    EmploymentStatus,
    LoanApplication,
    ApplicantInfo,
    FinancialInfo,
    LoanRequest,
    EligibilityResult
)
from ...services import EligibilityEngine, LLMService
from ...core.config import settings
from ...core.logging_config import conversation_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/eligibility", tags=["eligibility"])

# Initialize services
eligibility_engine = EligibilityEngine()
llm_service = LLMService()


class EligibilityCheckRequest(BaseModel):
    """Request model for eligibility check."""

    # Applicant Information
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None

    # Financial Information
    annual_income: float = Field(..., gt=0, description="Annual gross income in USD")
    monthly_expenses: float = Field(default=0, ge=0)
    employment_status: EmploymentStatus
    employer_name: Optional[str] = None
    years_employed: Optional[float] = Field(None, ge=0)
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    existing_debt: float = Field(default=0, ge=0)

    # Loan Request
    loan_type: LoanType
    requested_amount: float = Field(..., gt=0)
    loan_purpose: Optional[str] = None
    loan_term_months: int = Field(..., gt=0, le=360)
    collateral_value: Optional[float] = Field(None, ge=0)
    down_payment: Optional[float] = Field(None, ge=0)

    # Consent
    consent_given: bool = Field(..., description="User must consent to credit check")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15",
                "email": "john.doe@example.com",
                "annual_income": 75000,
                "employment_status": "employed",
                "years_employed": 5,
                "credit_score": 720,
                "existing_debt": 15000,
                "loan_type": "personal",
                "requested_amount": 25000,
                "loan_purpose": "Debt consolidation",
                "loan_term_months": 60,
                "consent_given": True
            }
        }


class EligibilityCheckResponse(BaseModel):
    """Response model for eligibility check."""

    session_id: str
    status: str
    loan_type: str
    requested_amount: float
    approved_amount: Optional[float] = None
    estimated_rate: Optional[float] = None
    estimated_monthly_payment: Optional[float] = None
    overall_score: float
    explanation: str
    factors: list
    next_steps: list
    disclaimers: list
    requires_human_review: bool


class QuickCheckRequest(BaseModel):
    """Simplified request for quick eligibility estimate."""

    loan_type: LoanType
    requested_amount: float = Field(..., gt=0)
    annual_income: float = Field(..., gt=0)
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    existing_debt: float = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "loan_type": "personal",
                "requested_amount": 20000,
                "annual_income": 60000,
                "credit_score": 700,
                "existing_debt": 5000
            }
        }


class QuickCheckResponse(BaseModel):
    """Response for quick eligibility check."""

    likely_eligible: bool
    confidence: str  # "high", "medium", "low"
    estimated_rate_range: str
    key_factors: list
    recommendation: str


@router.post("/check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    background_tasks: BackgroundTasks
) -> EligibilityCheckResponse:
    """
    Perform a comprehensive loan eligibility check.

    This endpoint evaluates all provided information against lending criteria
    and returns a detailed eligibility assessment including:
    - Eligibility status (eligible, conditionally eligible, needs review, not eligible)
    - Approved amount and estimated rate (if eligible)
    - Detailed factor analysis
    - Personalized next steps
    """
    if not request.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Consent is required to perform eligibility check"
        )

    try:
        # Build loan application from request
        import uuid
        session_id = str(uuid.uuid4())

        application = LoanApplication(
            session_id=session_id,
            applicant=ApplicantInfo(
                first_name=request.first_name,
                last_name=request.last_name,
                date_of_birth=request.date_of_birth,
                email=request.email,
                phone=request.phone,
            ),
            financial=FinancialInfo(
                annual_income=Decimal(str(request.annual_income)),
                monthly_expenses=Decimal(str(request.monthly_expenses)),
                employment_status=request.employment_status,
                employer_name=request.employer_name,
                years_employed=request.years_employed,
                credit_score=request.credit_score,
                existing_debt=Decimal(str(request.existing_debt)),
            ),
            loan=LoanRequest(
                loan_type=request.loan_type,
                requested_amount=Decimal(str(request.requested_amount)),
                loan_purpose=request.loan_purpose,
                loan_term_months=request.loan_term_months,
                collateral_value=Decimal(str(request.collateral_value)) if request.collateral_value else None,
                down_payment=Decimal(str(request.down_payment)) if request.down_payment else None,
            ),
            consent_given=request.consent_given
        )

        # Run eligibility check
        result = eligibility_engine.evaluate(application)

        # Generate LLM explanation asynchronously
        explanation = await llm_service.generate_eligibility_explanation(result)
        result.explanation = explanation

        # Log the check
        conversation_logger.log_eligibility_check(
            session_id=session_id,
            loan_type=request.loan_type.value,
            decision=result.status.value,
            factors={f.name: f.status for f in result.factors},
            response_time_ms=0  # Would be measured properly in production
        )

        return EligibilityCheckResponse(
            session_id=result.session_id,
            status=result.status.value,
            loan_type=result.loan_type.value,
            requested_amount=float(result.requested_amount),
            approved_amount=float(result.approved_amount) if result.approved_amount else None,
            estimated_rate=result.estimated_rate,
            estimated_monthly_payment=float(result.estimated_monthly_payment) if result.estimated_monthly_payment else None,
            overall_score=result.overall_score,
            explanation=result.explanation,
            factors=[f.dict() for f in result.factors],
            next_steps=result.next_steps,
            disclaimers=result.disclaimers,
            requires_human_review=result.requires_human_review
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Eligibility check failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@router.post("/quick-check", response_model=QuickCheckResponse)
async def quick_eligibility_check(request: QuickCheckRequest) -> QuickCheckResponse:
    """
    Perform a quick eligibility estimate with minimal information.

    This is useful for initial screening before collecting full application details.
    Returns a general likelihood of approval without making a formal decision.
    """
    try:
        # Simple eligibility logic for quick check
        credit_score = request.credit_score or 650
        dti = request.existing_debt / request.annual_income if request.annual_income > 0 else 1

        key_factors = []
        score = 0

        # Credit score factor
        if credit_score >= 740:
            score += 35
            key_factors.append("Excellent credit score")
        elif credit_score >= 670:
            score += 25
            key_factors.append("Good credit score")
        elif credit_score >= 580:
            score += 15
            key_factors.append("Fair credit score - may affect rate")
        else:
            key_factors.append("Credit score may need improvement")

        # DTI factor
        if dti < 0.3:
            score += 35
            key_factors.append("Low debt-to-income ratio")
        elif dti < 0.43:
            score += 25
            key_factors.append("Acceptable debt-to-income ratio")
        else:
            key_factors.append("High debt-to-income ratio")

        # Loan-to-income factor
        lti = request.requested_amount / request.annual_income
        if lti < 0.5:
            score += 30
            key_factors.append("Conservative loan amount relative to income")
        elif lti < 1:
            score += 20
        else:
            key_factors.append("Loan amount is high relative to income")

        # Determine rate range based on credit score
        if credit_score >= 750:
            rate_range = "5.99% - 8.99%"
        elif credit_score >= 700:
            rate_range = "9.99% - 12.99%"
        elif credit_score >= 650:
            rate_range = "13.99% - 17.99%"
        else:
            rate_range = "18.99% - 24.99%"

        # Determine likelihood and confidence
        if score >= 80:
            likely_eligible = True
            confidence = "high"
            recommendation = "You appear to be a strong candidate. We recommend completing the full application."
        elif score >= 50:
            likely_eligible = True
            confidence = "medium"
            recommendation = "You may qualify with some conditions. Complete the application for a detailed assessment."
        else:
            likely_eligible = False
            confidence = "low"
            recommendation = "Based on this quick check, you may want to improve some factors before applying. Consider speaking with an advisor."

        return QuickCheckResponse(
            likely_eligible=likely_eligible,
            confidence=confidence,
            estimated_rate_range=rate_range,
            key_factors=key_factors,
            recommendation=recommendation
        )

    except Exception as e:
        logger.error(f"Quick check failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@router.get("/loan-types")
async def get_loan_types():
    """Get available loan types and their basic criteria."""
    return {
        "loan_types": [
            {
                "type": "personal",
                "name": "Personal Loan",
                "description": "Unsecured loans for various personal needs",
                "min_amount": 1000,
                "max_amount": 50000,
                "term_range": "12-84 months",
                "min_credit_score": 620
            },
            {
                "type": "home",
                "name": "Home Loan",
                "description": "Mortgage loans for home purchase or refinance",
                "min_amount": 50000,
                "max_amount": 750000,
                "term_range": "120-360 months",
                "min_credit_score": 640
            },
            {
                "type": "auto",
                "name": "Auto Loan",
                "description": "Vehicle financing for new or used cars",
                "min_amount": 5000,
                "max_amount": 100000,
                "term_range": "24-84 months",
                "min_credit_score": 600
            },
            {
                "type": "business",
                "name": "Business Loan",
                "description": "Financing for business needs and expansion",
                "min_amount": 10000,
                "max_amount": 500000,
                "term_range": "12-120 months",
                "min_credit_score": 680
            },
            {
                "type": "education",
                "name": "Education Loan",
                "description": "Student loans for education expenses",
                "min_amount": 1000,
                "max_amount": 200000,
                "term_range": "60-240 months",
                "min_credit_score": 580
            }
        ]
    }
