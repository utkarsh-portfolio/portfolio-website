"""
Conversation Service
Manages conversation state, flow control, and orchestrates the loan pre-qualification process.
"""

import logging
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, Tuple, List

from ..models import (
    LoanType,
    EmploymentStatus,
    ApplicantInfo,
    FinancialInfo,
    LoanRequest,
    LoanApplication,
    ConversationState,
    EligibilityResult
)
from ..prompts import PromptTemplates
from ..core.logging_config import conversation_logger
from .eligibility_engine import EligibilityEngine
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Orchestrates the loan pre-qualification conversation flow.

    Manages:
    - Conversation state tracking
    - User input validation and entity extraction
    - Flow progression through pre-qualification steps
    - Integration with eligibility engine and LLM services
    """

    # Conversation flow steps
    FLOW_STEPS = [
        "greeting",
        "collect_loan_type",
        "collect_amount",
        "collect_term",
        "collect_income",
        "collect_employment",
        "collect_credit_score",
        "collect_debt",
        "confirm_details",
        "check_eligibility",
        "present_result",
        "next_steps"
    ]

    # Required fields for each loan type
    REQUIRED_FIELDS = {
        "common": [
            "loan_type", "requested_amount", "loan_term_months",
            "annual_income", "employment_status", "credit_score", "existing_debt"
        ],
        LoanType.HOME: ["collateral_value", "down_payment"],
        LoanType.AUTO: ["collateral_value"],
    }

    def __init__(
        self,
        eligibility_engine: Optional[EligibilityEngine] = None,
        llm_service: Optional[LLMService] = None
    ):
        """Initialize conversation service with dependencies."""
        self.eligibility_engine = eligibility_engine or EligibilityEngine()
        self.llm_service = llm_service or LLMService()
        self.sessions: Dict[str, ConversationState] = {}

    def create_session(self) -> ConversationState:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        state = ConversationState(
            session_id=session_id,
            current_step="greeting",
            collected_data={},
            missing_fields=self.REQUIRED_FIELDS["common"].copy()
        )
        self.sessions[session_id] = state
        logger.info(f"Created new session: {session_id}")
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Retrieve existing session."""
        return self.sessions.get(session_id)

    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> Tuple[str, ConversationState]:
        """
        Process a user message and generate response.

        Args:
            session_id: The conversation session ID
            user_message: The user's message

        Returns:
            Tuple of (response_text, updated_state)
        """
        state = self.get_session(session_id)
        if not state:
            state = self.create_session()
            state.session_id = session_id
            self.sessions[session_id] = state

        # Add user message to history
        state.add_message("user", user_message)

        # Extract intent and entities
        intent = self._detect_intent(user_message, state)
        entities = self._extract_entities(user_message, state)

        conversation_logger.log_intent(
            session_id=session_id,
            intent=intent,
            confidence=0.9,  # Placeholder - would come from NLU
            parameters=entities
        )

        # Handle special intents
        if intent == "handoff_request":
            response = self._handle_handoff_request(state)
        elif intent == "out_of_scope":
            response = self._handle_out_of_scope(state)
        elif intent == "correction":
            response = self._handle_correction(user_message, state)
        else:
            # Update collected data with extracted entities
            self._update_collected_data(entities, state)

            # Progress conversation flow
            response = await self._progress_flow(state)

        # Add response to history
        state.add_message("assistant", response)

        return response, state

    def _detect_intent(self, message: str, state: ConversationState) -> str:
        """Detect user intent from message."""
        message_lower = message.lower().strip()

        # Check for handoff request
        handoff_keywords = ["human", "person", "agent", "representative", "speak to someone", "talk to"]
        if any(kw in message_lower for kw in handoff_keywords):
            return "handoff_request"

        # Check for confirmation
        if message_lower in ["yes", "correct", "that's right", "confirm", "looks good", "yep", "yeah"]:
            return "confirmation"

        # Check for correction
        if message_lower in ["no", "wrong", "incorrect", "that's wrong", "not right", "nope"]:
            return "correction"

        # Check for loan type mention
        loan_types = ["personal", "home", "mortgage", "auto", "car", "business", "education", "student"]
        if any(lt in message_lower for lt in loan_types):
            return "loan_inquiry"

        # Check for numeric values (amount, income, etc.)
        if re.search(r'\$?\d+[,\d]*\.?\d*', message):
            step = state.current_step
            if step == "collect_amount":
                return "amount_provided"
            elif step == "collect_term":
                return "term_provided"
            elif step == "collect_income":
                return "income_provided"
            elif step == "collect_credit_score":
                return "credit_score_provided"
            elif step == "collect_debt":
                return "debt_provided"
            return "numeric_value"

        # Check for employment status
        employment_keywords = {
            "employed": ["employed", "work", "job", "working"],
            "self_employed": ["self-employed", "self employed", "own business", "freelance"],
            "unemployed": ["unemployed", "not working", "between jobs"],
            "retired": ["retired", "retirement"],
            "student": ["student", "studying", "school", "college", "university"]
        }
        for status, keywords in employment_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return "employment_provided"

        return "general_response"

    def _extract_entities(self, message: str, state: ConversationState) -> Dict[str, Any]:
        """Extract entities from user message."""
        entities = {}
        message_lower = message.lower()

        # Extract loan type
        loan_type_map = {
            "personal": LoanType.PERSONAL,
            "home": LoanType.HOME,
            "mortgage": LoanType.HOME,
            "auto": LoanType.AUTO,
            "car": LoanType.AUTO,
            "business": LoanType.BUSINESS,
            "education": LoanType.EDUCATION,
            "student": LoanType.EDUCATION,
        }
        for keyword, loan_type in loan_type_map.items():
            if keyword in message_lower:
                entities["loan_type"] = loan_type
                break

        # Extract monetary amounts
        amount_match = re.search(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)\s*(?:k|K|thousand)?', message)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                amount = Decimal(amount_str)
                if "k" in message_lower or "thousand" in message_lower:
                    amount *= 1000
                entities["amount"] = amount
            except InvalidOperation:
                pass

        # Extract loan term (months/years)
        term_match = re.search(r'(\d+)\s*(month|year|yr)s?', message_lower)
        if term_match:
            term_value = int(term_match.group(1))
            term_unit = term_match.group(2)
            if "year" in term_unit or "yr" in term_unit:
                term_value *= 12
            entities["loan_term_months"] = term_value

        # Extract credit score
        credit_match = re.search(r'\b([3-8]\d{2})\b', message)
        if credit_match:
            score = int(credit_match.group(1))
            if 300 <= score <= 850:
                entities["credit_score"] = score

        # Extract employment status
        employment_map = {
            "employed": EmploymentStatus.EMPLOYED,
            "self-employed": EmploymentStatus.SELF_EMPLOYED,
            "self employed": EmploymentStatus.SELF_EMPLOYED,
            "unemployed": EmploymentStatus.UNEMPLOYED,
            "retired": EmploymentStatus.RETIRED,
            "student": EmploymentStatus.STUDENT,
        }
        for keyword, status in employment_map.items():
            if keyword in message_lower:
                entities["employment_status"] = status
                break

        return entities

    def _update_collected_data(self, entities: Dict[str, Any], state: ConversationState):
        """Update collected data with new entities."""
        field_mapping = {
            "loan_type": "loan_type",
            "amount": "requested_amount",
            "loan_term_months": "loan_term_months",
            "credit_score": "credit_score",
            "employment_status": "employment_status",
        }

        for entity_key, value in entities.items():
            field_key = field_mapping.get(entity_key, entity_key)
            state.collected_data[field_key] = value

            # Remove from missing fields if present
            if field_key in state.missing_fields:
                state.missing_fields.remove(field_key)

        # Handle amount based on current step
        if "amount" in entities:
            step = state.current_step
            if step == "collect_amount":
                state.collected_data["requested_amount"] = entities["amount"]
                if "requested_amount" in state.missing_fields:
                    state.missing_fields.remove("requested_amount")
            elif step == "collect_income":
                state.collected_data["annual_income"] = entities["amount"]
                if "annual_income" in state.missing_fields:
                    state.missing_fields.remove("annual_income")
            elif step == "collect_debt":
                state.collected_data["existing_debt"] = entities["amount"]
                if "existing_debt" in state.missing_fields:
                    state.missing_fields.remove("existing_debt")

    async def _progress_flow(self, state: ConversationState) -> str:
        """Progress the conversation flow and generate appropriate response."""
        current_step = state.current_step
        collected = state.collected_data

        # Determine next step based on current state
        if current_step == "greeting":
            state.current_step = "collect_loan_type"
            return PromptTemplates.get_greeting()

        elif current_step == "collect_loan_type":
            if "loan_type" in collected:
                state.current_step = "collect_amount"
                loan_type = collected["loan_type"]
                return PromptTemplates.COLLECT_LOAN_DETAILS.substitute(
                    loan_type=loan_type.value
                )
            return "What type of loan are you interested in? We offer personal, home, auto, business, and education loans."

        elif current_step == "collect_amount":
            if "requested_amount" in collected:
                # Set default term if not provided
                if "loan_term_months" not in collected:
                    collected["loan_term_months"] = 60  # Default 5 years
                state.current_step = "collect_income"
                return PromptTemplates.COLLECT_INCOME.substitute(
                    amount=f"{float(collected['requested_amount']):,.0f}",
                    loan_type=collected.get("loan_type", LoanType.PERSONAL).value,
                    term=collected.get("loan_term_months", 60)
                )
            return "How much would you like to borrow? Please provide the loan amount."

        elif current_step == "collect_income":
            if "annual_income" in collected:
                state.current_step = "collect_employment"
                return PromptTemplates.COLLECT_EMPLOYMENT.substitute()
            return "What is your approximate annual income before taxes?"

        elif current_step == "collect_employment":
            if "employment_status" in collected:
                state.current_step = "collect_credit_score"
                emp_status = collected["employment_status"]
                emp_response = f"Got it, you're {emp_status.value.replace('_', ' ')}."
                return PromptTemplates.COLLECT_CREDIT_SCORE.substitute(
                    employment_response=emp_response
                )
            return "What is your current employment status? (Employed, Self-employed, Retired, Student, or Unemployed)"

        elif current_step == "collect_credit_score":
            if "credit_score" in collected or "i don't know" in str(state.conversation_history[-1].get("content", "")).lower():
                if "credit_score" not in collected:
                    collected["credit_score"] = 650  # Default estimate
                state.current_step = "collect_debt"
                return PromptTemplates.COLLECT_DEBT.substitute()
            return "Do you know your approximate credit score? (300-850, or say 'I don't know')"

        elif current_step == "collect_debt":
            if "existing_debt" in collected or "none" in str(state.conversation_history[-1].get("content", "")).lower():
                if "existing_debt" not in collected:
                    collected["existing_debt"] = Decimal("0")
                state.current_step = "confirm_details"
                return self._generate_confirmation(state)
            return "What is your approximate total existing debt? (or 'none' if you have no debt)"

        elif current_step == "confirm_details":
            last_message = state.conversation_history[-1].get("content", "").lower()
            if "yes" in last_message or "correct" in last_message or "confirm" in last_message:
                state.current_step = "check_eligibility"
                return await self._check_eligibility(state)
            elif "no" in last_message or "wrong" in last_message:
                return "What would you like to correct? Please let me know which information needs to be updated."
            return "Please confirm if the information above is correct by saying 'yes' or 'no'."

        elif current_step in ["check_eligibility", "present_result"]:
            return await self._check_eligibility(state)

        return "I'm here to help with your loan pre-qualification. Could you tell me more about what you're looking for?"

    def _generate_confirmation(self, state: ConversationState) -> str:
        """Generate confirmation message with collected data."""
        data = state.collected_data

        return PromptTemplates.CONFIRM_DETAILS.substitute(
            loan_type=data.get("loan_type", LoanType.PERSONAL).value.title(),
            amount=f"{float(data.get('requested_amount', 0)):,.0f}",
            term=data.get("loan_term_months", 60),
            income=f"{float(data.get('annual_income', 0)):,.0f}",
            employment=data.get("employment_status", EmploymentStatus.EMPLOYED).value.replace("_", " ").title(),
            credit_score=data.get("credit_score", "Not provided"),
            debt=f"{float(data.get('existing_debt', 0)):,.0f}",
            disclaimer=PromptTemplates.DISCLAIMERS["privacy"]
        )

    async def _check_eligibility(self, state: ConversationState) -> str:
        """Run eligibility check and generate result message."""
        data = state.collected_data
        start_time = datetime.utcnow()

        # Build application from collected data
        try:
            application = LoanApplication(
                session_id=state.session_id,
                applicant=ApplicantInfo(
                    first_name="Applicant",  # Placeholder
                    last_name="User",
                    date_of_birth=date(1990, 1, 1),  # Placeholder
                ),
                financial=FinancialInfo(
                    annual_income=data.get("annual_income", Decimal("0")),
                    monthly_expenses=Decimal("0"),
                    employment_status=data.get("employment_status", EmploymentStatus.EMPLOYED),
                    credit_score=data.get("credit_score"),
                    existing_debt=data.get("existing_debt", Decimal("0")),
                ),
                loan=LoanRequest(
                    loan_type=data.get("loan_type", LoanType.PERSONAL),
                    requested_amount=data.get("requested_amount", Decimal("10000")),
                    loan_term_months=data.get("loan_term_months", 60),
                    collateral_value=data.get("collateral_value"),
                    down_payment=data.get("down_payment"),
                ),
                consent_given=True
            )
        except Exception as e:
            logger.error(f"Failed to build application: {e}")
            return "I encountered an issue processing your information. Would you like to try again or speak with a representative?"

        # Run eligibility check
        result = self.eligibility_engine.evaluate(application)

        # Generate LLM explanation
        explanation = await self.llm_service.generate_eligibility_explanation(result)
        result.explanation = explanation

        # Log the result
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        conversation_logger.log_eligibility_check(
            session_id=state.session_id,
            loan_type=result.loan_type.value,
            decision=result.status.value,
            factors={f.name: f.status for f in result.factors},
            response_time_ms=response_time_ms
        )

        # Update state
        state.current_step = "present_result"
        state.collected_data["eligibility_result"] = result.dict()

        # Generate response
        offer_details = None
        if result.approved_amount:
            offer_details = (
                f"\n**Pre-Approved Offer:**\n"
                f"• Amount: ${float(result.approved_amount):,.2f}\n"
                f"• Estimated Rate: {result.estimated_rate:.2%}\n"
                f"• Monthly Payment: ${float(result.estimated_monthly_payment):,.2f}"
            )

        return PromptTemplates.get_eligibility_result(
            status=result.status.value,
            explanation=explanation,
            factors=[f.dict() for f in result.factors],
            offer_details=offer_details,
            next_steps=result.next_steps
        )

    def _handle_handoff_request(self, state: ConversationState) -> str:
        """Handle request to speak with human."""
        conversation_logger.log_handoff(state.session_id, "user_requested")

        return PromptTemplates.HANDOFF_TO_HUMAN.substitute(
            reason="I'd be happy to connect you with one of our loan specialists.",
            hours="Mon-Fri 8am-8pm, Sat 9am-5pm EST"
        )

    def _handle_out_of_scope(self, state: ConversationState) -> str:
        """Handle out-of-scope requests."""
        return (
            "I'm specialized in helping with loan pre-qualification. "
            "For other banking services or questions, I can connect you with "
            "the right department. Would you like to continue with your loan inquiry, "
            "or would you prefer to speak with a representative?"
        )

    def _handle_correction(self, message: str, state: ConversationState) -> str:
        """Handle request to correct information."""
        return (
            "No problem! What information would you like to correct? "
            "You can update:\n"
            "• Loan amount\n"
            "• Income\n"
            "• Employment status\n"
            "• Credit score\n"
            "• Existing debt\n\n"
            "Just let me know what needs to be changed."
        )
