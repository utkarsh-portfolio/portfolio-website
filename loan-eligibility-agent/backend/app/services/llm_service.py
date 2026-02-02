"""
LLM Service
Handles natural language generation for eligibility explanations and conversational responses.
Supports both Google Vertex AI and OpenAI backends.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from ..core.config import settings
from ..models import EligibilityResult, EligibilityStatus, ConversationState

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text from prompt."""
        pass


class VertexAIProvider(LLMProvider):
    """Google Vertex AI LLM provider."""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_LOCATION
        self.model = settings.VERTEX_AI_MODEL
        self._client = None

    async def _get_client(self):
        """Lazy initialize Vertex AI client."""
        if self._client is None:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                vertexai.init(project=self.project_id, location=self.location)
                self._client = GenerativeModel(self.model)
            except ImportError:
                logger.warning("Vertex AI SDK not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise
        return self._client

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using Vertex AI."""
        try:
            client = await self._get_client()
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = await client.generate_content_async(
                full_prompt,
                generation_config={
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_output_tokens": settings.LLM_MAX_TOKENS,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI generation failed: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self._client = None

    async def _get_client(self):
        """Lazy initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI SDK not installed")
                raise
        return self._client

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using OpenAI."""
        try:
            client = await self._get_client()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and demo purposes."""

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a mock response."""
        # Simple keyword-based response generation for demo
        if "eligible" in prompt.lower():
            return "Based on your application, you appear to meet our lending criteria."
        elif "not eligible" in prompt.lower():
            return "Unfortunately, your application does not meet our current lending criteria."
        else:
            return "Thank you for your inquiry. How can I assist you further?"


class LLMService:
    """
    Service for generating natural language content for the loan eligibility agent.

    This service handles:
    - Eligibility explanation generation
    - Conversational response generation
    - Intent-specific response crafting
    """

    SYSTEM_PROMPT = """You are a helpful, professional loan advisor assistant for a financial institution.
Your role is to explain loan eligibility decisions clearly and empathetically.

Guidelines:
- Be professional but warm and approachable
- Explain financial concepts in simple terms
- Never guarantee loan approval - always use qualifying language
- Be transparent about factors affecting eligibility
- Suggest actionable next steps
- Include appropriate disclaimers
- If someone is not eligible, be empathetic and offer alternatives
- Never provide specific financial advice - recommend speaking with a loan specialist
- Protect customer privacy - never repeat sensitive information unnecessarily
"""

    def __init__(self, provider: Optional[LLMProvider] = None):
        """Initialize LLM service with specified provider."""
        if provider:
            self.provider = provider
        elif settings.OPENAI_API_KEY:
            self.provider = OpenAIProvider()
        elif settings.GCP_PROJECT_ID:
            self.provider = VertexAIProvider()
        else:
            logger.warning("No LLM provider configured, using mock provider")
            self.provider = MockLLMProvider()

    async def generate_eligibility_explanation(
        self,
        result: EligibilityResult
    ) -> str:
        """
        Generate a natural language explanation of the eligibility result.

        Args:
            result: The eligibility assessment result

        Returns:
            Human-readable explanation of the decision
        """
        prompt = self._build_explanation_prompt(result)

        try:
            explanation = await self.provider.generate(prompt, self.SYSTEM_PROMPT)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return self._get_fallback_explanation(result)

    async def generate_conversational_response(
        self,
        user_message: str,
        conversation_state: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a conversational response based on user input and context.

        Args:
            user_message: The user's message
            conversation_state: Current conversation state
            context: Additional context for response generation

        Returns:
            Natural language response
        """
        prompt = self._build_conversation_prompt(
            user_message, conversation_state, context
        )

        try:
            response = await self.provider.generate(prompt, self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "I apologize, but I'm having trouble processing your request. Would you like to speak with a human representative?"

    async def explain_rejection_reason(
        self,
        factors: List[Dict[str, Any]]
    ) -> str:
        """
        Generate an empathetic explanation for loan rejection.

        Args:
            factors: List of factors that led to rejection

        Returns:
            Empathetic explanation with improvement suggestions
        """
        failed_factors = [f for f in factors if f.get("status") == "fail"]

        prompt = f"""A loan application was not approved due to the following factors:

{self._format_factors(failed_factors)}

Please provide an empathetic explanation that:
1. Acknowledges the applicant's situation
2. Clearly explains each factor in simple terms
3. Provides specific, actionable steps to improve eligibility
4. Mentions alternative options they might consider
5. Offers to connect them with a loan specialist for personalized guidance

Keep the tone supportive and solution-oriented."""

        try:
            return await self.provider.generate(prompt, self.SYSTEM_PROMPT)
        except Exception:
            return self._get_fallback_rejection_explanation(failed_factors)

    def _build_explanation_prompt(self, result: EligibilityResult) -> str:
        """Build prompt for eligibility explanation."""
        status_text = {
            EligibilityStatus.ELIGIBLE: "approved for pre-qualification",
            EligibilityStatus.CONDITIONALLY_ELIGIBLE: "conditionally approved",
            EligibilityStatus.NOT_ELIGIBLE: "not approved at this time",
            EligibilityStatus.NEEDS_REVIEW: "requires additional review"
        }

        factors_text = self._format_factors([f.dict() for f in result.factors])

        prompt = f"""Generate a clear, professional explanation for a loan eligibility decision.

Decision: The applicant is {status_text[result.status]}
Loan Type: {result.loan_type.value}
Requested Amount: ${float(result.requested_amount):,.2f}
{f"Pre-approved Amount: ${float(result.approved_amount):,.2f}" if result.approved_amount else ""}
{f"Estimated Rate: {result.estimated_rate:.2%}" if result.estimated_rate else ""}
{f"Estimated Monthly Payment: ${float(result.estimated_monthly_payment):,.2f}" if result.estimated_monthly_payment else ""}
Overall Score: {result.overall_score}/100

Assessment Factors:
{factors_text}

Next Steps:
{chr(10).join(f"- {step}" for step in result.next_steps)}

Please write a 2-3 paragraph explanation that:
1. Summarizes the decision clearly
2. Highlights key factors (positive and negative)
3. Explains what the numbers mean in plain language
4. Guides them on next steps

Do not repeat the exact numbers unless necessary for clarity. Focus on the "why" behind the decision."""

        return prompt

    def _build_conversation_prompt(
        self,
        user_message: str,
        state: ConversationState,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for conversational response."""
        history = "\n".join(
            f"{msg['role'].title()}: {msg['content']}"
            for msg in state.conversation_history[-5:]  # Last 5 messages
        )

        prompt = f"""Current conversation step: {state.current_step}
Data collected so far: {state.collected_data}
Missing information: {state.missing_fields}

Recent conversation:
{history}

User's latest message: "{user_message}"

{f"Additional context: {context}" if context else ""}

Generate an appropriate response that:
1. Addresses the user's message directly
2. Moves the conversation forward
3. Collects any missing information naturally
4. Maintains a helpful, professional tone

If the user is asking about something outside loan eligibility, politely redirect to the loan pre-qualification process."""

        return prompt

    def _format_factors(self, factors: List[Dict[str, Any]]) -> str:
        """Format factors for prompt inclusion."""
        lines = []
        for f in factors:
            status_emoji = {"pass": "✓", "warning": "⚠", "fail": "✗"}.get(
                f.get("status", ""), "•"
            )
            lines.append(f"{status_emoji} {f.get('name', 'Unknown')}: {f.get('message', '')}")
        return "\n".join(lines)

    def _get_fallback_explanation(self, result: EligibilityResult) -> str:
        """Get fallback explanation when LLM fails."""
        if result.status == EligibilityStatus.ELIGIBLE:
            return (
                f"Great news! Based on the information provided, you pre-qualify for a "
                f"{result.loan_type.value} loan. Your estimated rate is "
                f"{result.estimated_rate:.2%} with monthly payments around "
                f"${float(result.estimated_monthly_payment):,.2f}. "
                f"Please note this is a preliminary assessment and final approval "
                f"is subject to verification."
            )
        elif result.status == EligibilityStatus.NOT_ELIGIBLE:
            return (
                "Thank you for your interest. Based on our current lending criteria, "
                "we're unable to pre-qualify you for this loan at this time. "
                "We encourage you to review the factors affecting your eligibility "
                "and consider speaking with one of our loan specialists about "
                "alternative options."
            )
        else:
            return (
                "Your application requires additional review. One of our loan "
                "specialists will contact you within 24-48 hours to discuss "
                "your options and next steps."
            )

    def _get_fallback_rejection_explanation(
        self,
        failed_factors: List[Dict[str, Any]]
    ) -> str:
        """Get fallback rejection explanation."""
        reasons = ", ".join(f.get("name", "unknown factor") for f in failed_factors)
        return (
            f"We were unable to approve your application at this time due to: {reasons}. "
            "We understand this may be disappointing. We encourage you to speak with "
            "one of our loan specialists who can provide personalized guidance on "
            "improving your eligibility or exploring alternative options."
        )
