"""
Webhook API Routes
Endpoints for Dialogflow CX webhook fulfillment.
"""

import logging
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel

from ...services import ConversationService, EligibilityEngine
from ...models import (
    LoanType,
    EmploymentStatus,
    LoanApplication,
    ApplicantInfo,
    FinancialInfo,
    LoanRequest
)
from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

# Initialize services
conversation_service = ConversationService()
eligibility_engine = EligibilityEngine()


class DialogflowRequest(BaseModel):
    """Dialogflow CX webhook request structure."""
    detectIntentResponseId: Optional[str] = None
    intentInfo: Optional[Dict[str, Any]] = None
    pageInfo: Optional[Dict[str, Any]] = None
    sessionInfo: Optional[Dict[str, Any]] = None
    fulfillmentInfo: Optional[Dict[str, Any]] = None
    messages: Optional[list] = None
    payload: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    languageCode: Optional[str] = "en"


class DialogflowResponse(BaseModel):
    """Dialogflow CX webhook response structure."""
    fulfillmentResponse: Optional[Dict[str, Any]] = None
    pageInfo: Optional[Dict[str, Any]] = None
    sessionInfo: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None


def create_text_response(text: str) -> Dict[str, Any]:
    """Create a text response for Dialogflow."""
    return {
        "fulfillmentResponse": {
            "messages": [
                {
                    "text": {
                        "text": [text]
                    }
                }
            ]
        }
    }


def create_response_with_params(
    text: str,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a response with session parameters."""
    response = create_text_response(text)
    if parameters:
        response["sessionInfo"] = {
            "parameters": parameters
        }
    return response


@router.post("/dialogflow")
async def dialogflow_webhook(
    request: Request,
    x_goog_signature: Optional[str] = Header(None)
):
    """
    Dialogflow CX webhook fulfillment endpoint.

    This endpoint handles:
    - Intent fulfillment
    - Parameter validation
    - Eligibility checks
    - Dynamic response generation
    """
    try:
        body = await request.json()
        logger.info(f"Received Dialogflow webhook: {body.get('intentInfo', {}).get('displayName', 'unknown')}")

        # Parse request
        session_info = body.get("sessionInfo", {})
        session_id = session_info.get("session", "").split("/")[-1]
        parameters = session_info.get("parameters", {})

        intent_info = body.get("intentInfo", {})
        intent_name = intent_info.get("displayName", "")

        fulfillment_info = body.get("fulfillmentInfo", {})
        tag = fulfillment_info.get("tag", "")

        # Route based on fulfillment tag
        if tag == "validate_loan_amount":
            return await handle_validate_loan_amount(parameters)
        elif tag == "validate_income":
            return await handle_validate_income(parameters)
        elif tag == "validate_credit_score":
            return await handle_validate_credit_score(parameters)
        elif tag == "check_eligibility":
            return await handle_eligibility_check(session_id, parameters)
        elif tag == "explain_rejection":
            return await handle_explain_rejection(parameters)
        elif tag == "calculate_payment":
            return await handle_calculate_payment(parameters)
        elif tag == "human_handoff":
            return await handle_human_handoff(session_id, parameters)
        else:
            # Default fulfillment
            return create_text_response(
                "I'm here to help with your loan pre-qualification. What would you like to know?"
            )

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return create_text_response(
            "I apologize, but I encountered an issue. Would you like to try again or speak with a representative?"
        )


async def handle_validate_loan_amount(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the requested loan amount."""
    amount = parameters.get("loan_amount", 0)
    loan_type = parameters.get("loan_type", "personal")

    # Get limits for loan type
    limits = {
        "personal": (1000, 50000),
        "home": (50000, 750000),
        "auto": (5000, 100000),
        "business": (10000, 500000),
        "education": (1000, 200000)
    }

    min_amount, max_amount = limits.get(loan_type, (1000, 50000))

    if amount < min_amount:
        return create_response_with_params(
            f"The minimum loan amount for a {loan_type} loan is ${min_amount:,}. "
            f"Would you like to adjust your request?",
            {"amount_valid": False}
        )
    elif amount > max_amount:
        return create_response_with_params(
            f"The maximum loan amount for a {loan_type} loan is ${max_amount:,}. "
            f"Would you like to request a different amount?",
            {"amount_valid": False}
        )
    else:
        return create_response_with_params(
            f"Great! ${amount:,.0f} is within our lending range for {loan_type} loans.",
            {"amount_valid": True, "validated_amount": amount}
        )


async def handle_validate_income(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate income information."""
    income = parameters.get("annual_income", 0)
    loan_amount = parameters.get("loan_amount", 0)

    if income <= 0:
        return create_response_with_params(
            "I need a valid income amount. What is your annual income before taxes?",
            {"income_valid": False}
        )

    # Basic affordability check
    loan_to_income = loan_amount / income if income > 0 else float('inf')

    if loan_to_income > 5:
        return create_response_with_params(
            f"Based on your income of ${income:,.0f}, you may want to consider a smaller loan amount. "
            f"Would you like to proceed or adjust your request?",
            {"income_valid": True, "affordability_warning": True}
        )
    else:
        return create_response_with_params(
            f"Thank you. Your income of ${income:,.0f} has been recorded.",
            {"income_valid": True, "validated_income": income}
        )


async def handle_validate_credit_score(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and categorize credit score."""
    score = parameters.get("credit_score")

    if score is None or score == "unknown":
        return create_response_with_params(
            "No problem! We can proceed without your exact credit score. "
            "We'll use an estimate for this pre-qualification.",
            {"credit_score_provided": False, "estimated_score": 650}
        )

    try:
        score = int(score)
        if score < 300 or score > 850:
            return create_response_with_params(
                "Credit scores typically range from 300 to 850. "
                "Could you please verify your score?",
                {"credit_score_valid": False}
            )

        # Categorize score
        if score >= 750:
            category = "excellent"
        elif score >= 700:
            category = "good"
        elif score >= 650:
            category = "fair"
        else:
            category = "needs_improvement"

        return create_response_with_params(
            f"Your credit score of {score} is in the {category.replace('_', ' ')} range.",
            {
                "credit_score_valid": True,
                "validated_score": score,
                "score_category": category
            }
        )
    except ValueError:
        return create_response_with_params(
            "I couldn't understand that credit score. Please provide a number between 300 and 850.",
            {"credit_score_valid": False}
        )


async def handle_eligibility_check(
    session_id: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Perform eligibility check based on collected parameters."""
    try:
        # Build application from Dialogflow parameters
        loan_type_str = parameters.get("loan_type", "personal")
        loan_type = LoanType(loan_type_str) if loan_type_str in [lt.value for lt in LoanType] else LoanType.PERSONAL

        employment_str = parameters.get("employment_status", "employed")
        employment_map = {
            "employed": EmploymentStatus.EMPLOYED,
            "self-employed": EmploymentStatus.SELF_EMPLOYED,
            "self_employed": EmploymentStatus.SELF_EMPLOYED,
            "unemployed": EmploymentStatus.UNEMPLOYED,
            "retired": EmploymentStatus.RETIRED,
            "student": EmploymentStatus.STUDENT
        }
        employment = employment_map.get(employment_str, EmploymentStatus.EMPLOYED)

        application = LoanApplication(
            session_id=session_id,
            applicant=ApplicantInfo(
                first_name=parameters.get("first_name", "User"),
                last_name=parameters.get("last_name", ""),
                date_of_birth=date(1990, 1, 1),  # Placeholder
            ),
            financial=FinancialInfo(
                annual_income=Decimal(str(parameters.get("annual_income", 50000))),
                monthly_expenses=Decimal(str(parameters.get("monthly_expenses", 0))),
                employment_status=employment,
                credit_score=parameters.get("credit_score") or parameters.get("estimated_score"),
                existing_debt=Decimal(str(parameters.get("existing_debt", 0))),
            ),
            loan=LoanRequest(
                loan_type=loan_type,
                requested_amount=Decimal(str(parameters.get("loan_amount", 10000))),
                loan_term_months=parameters.get("loan_term", 60),
                collateral_value=Decimal(str(parameters.get("collateral_value", 0))) if parameters.get("collateral_value") else None,
                down_payment=Decimal(str(parameters.get("down_payment", 0))) if parameters.get("down_payment") else None,
            ),
            consent_given=True
        )

        # Run eligibility check
        result = eligibility_engine.evaluate(application)

        # Build response based on result
        if result.status.value == "eligible":
            response_text = (
                f"Great news! Based on your information, you pre-qualify for a "
                f"{loan_type.value} loan of up to ${float(result.approved_amount):,.0f}. "
                f"Your estimated rate is {result.estimated_rate:.2%} with monthly payments "
                f"around ${float(result.estimated_monthly_payment):,.0f}. "
                f"Would you like to proceed with a full application?"
            )
        elif result.status.value == "conditionally_eligible":
            response_text = (
                f"You may qualify for a {loan_type.value} loan with some conditions. "
                f"We could potentially approve ${float(result.approved_amount):,.0f}. "
                f"Would you like to discuss your options with a loan specialist?"
            )
        elif result.status.value == "needs_review":
            response_text = (
                "Your application requires additional review by our team. "
                "A loan specialist will contact you within 24-48 hours. "
                "Is there anything else I can help you with?"
            )
        else:
            response_text = (
                "Based on our current criteria, we're unable to pre-qualify you at this time. "
                "However, there may be other options available. "
                "Would you like to speak with a loan specialist about alternatives?"
            )

        return create_response_with_params(
            response_text,
            {
                "eligibility_status": result.status.value,
                "approved_amount": float(result.approved_amount) if result.approved_amount else 0,
                "estimated_rate": result.estimated_rate or 0,
                "eligibility_score": result.overall_score
            }
        )

    except Exception as e:
        logger.error(f"Eligibility check failed: {e}")
        return create_text_response(
            "I encountered an issue checking your eligibility. "
            "Would you like me to connect you with a loan specialist?"
        )


async def handle_explain_rejection(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Provide explanation for rejection and suggestions for improvement."""
    reasons = []

    credit_score = parameters.get("credit_score", 650)
    if credit_score and credit_score < 620:
        reasons.append(
            "Your credit score is below our minimum requirement. "
            "Consider working on improving your credit by paying bills on time "
            "and reducing outstanding balances."
        )

    dti = parameters.get("debt_to_income", 0)
    if dti and dti > 0.43:
        reasons.append(
            "Your debt-to-income ratio is higher than our guidelines allow. "
            "Paying down existing debt could improve your eligibility."
        )

    income = parameters.get("annual_income", 0)
    loan_amount = parameters.get("loan_amount", 0)
    if loan_amount and income and (loan_amount / income) > 2:
        reasons.append(
            "The requested loan amount is high relative to your income. "
            "You might consider a smaller loan or exploring income-driven options."
        )

    if not reasons:
        reasons.append(
            "Several factors contributed to this decision. "
            "A loan specialist can provide more specific guidance."
        )

    response_text = (
        "I understand this isn't the news you were hoping for. "
        f"Here's what affected your eligibility:\n\n"
        + "\n\n".join(f"• {reason}" for reason in reasons)
        + "\n\nWould you like to speak with a specialist about your options?"
    )

    return create_text_response(response_text)


async def handle_calculate_payment(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate estimated monthly payment."""
    amount = parameters.get("loan_amount", 10000)
    rate = parameters.get("interest_rate", 0.10)
    term = parameters.get("loan_term", 60)

    # Monthly payment calculation
    monthly_rate = rate / 12
    if monthly_rate > 0:
        payment = amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
    else:
        payment = amount / term

    total_interest = (payment * term) - amount

    response_text = (
        f"For a ${amount:,.0f} loan over {term} months at {rate:.2%} APR:\n\n"
        f"• Monthly Payment: ${payment:,.2f}\n"
        f"• Total Interest: ${total_interest:,.2f}\n"
        f"• Total Cost: ${payment * term:,.2f}\n\n"
        f"Would you like to adjust the loan amount or term?"
    )

    return create_response_with_params(
        response_text,
        {
            "monthly_payment": round(payment, 2),
            "total_interest": round(total_interest, 2)
        }
    )


async def handle_human_handoff(
    session_id: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle request for human assistance."""
    from ...core.logging_config import conversation_logger
    conversation_logger.log_handoff(session_id, "dialogflow_handoff")

    return {
        "fulfillmentResponse": {
            "messages": [
                {
                    "text": {
                        "text": [
                            "I'll connect you with a loan specialist who can provide personalized assistance. "
                            "Please hold while I transfer you."
                        ]
                    }
                }
            ]
        },
        "targetPage": "projects/-/locations/-/agents/-/flows/-/pages/human_handoff"
    }
