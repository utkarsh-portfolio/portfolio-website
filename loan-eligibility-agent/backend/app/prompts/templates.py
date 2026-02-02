"""
Prompt Templates
Centralized prompt templates for LLM interactions.
Implements prompt engineering best practices for financial services.
"""

from typing import Dict, Any, Optional
from string import Template


class PromptTemplates:
    """Collection of prompt templates for various conversation scenarios."""

    # System prompts for different contexts
    SYSTEM_PROMPTS = {
        "eligibility_advisor": """You are a professional loan eligibility advisor at a trusted financial institution.

Your responsibilities:
- Guide customers through the loan pre-qualification process
- Explain financial concepts in simple, accessible language
- Collect required information conversationally
- Provide clear, accurate eligibility assessments
- Maintain regulatory compliance in all responses

Communication style:
- Professional yet approachable
- Empathetic and understanding
- Clear and concise
- Solution-oriented

Important rules:
- Never guarantee loan approval
- Always include appropriate disclaimers
- Protect customer privacy
- Recommend speaking with a specialist for complex situations
- Stay within the scope of loan pre-qualification""",

        "document_collector": """You are helping a customer gather documents for their loan application.

Be specific about:
- What documents are needed
- Why each document is required
- Acceptable formats and alternatives
- How to securely submit documents

Be patient and helpful if customers have questions about documentation.""",

        "objection_handler": """You are handling customer concerns about the loan process.

Approach:
- Listen and acknowledge their concerns
- Provide clear, honest information
- Offer alternatives when possible
- Never pressure customers
- Know when to involve a human specialist"""
    }

    # Conversation flow templates
    GREETING = Template("""Welcome to our loan pre-qualification service! I'm here to help you understand your loan options.

I can help you check your eligibility for:
• Personal loans
• Home loans
• Auto loans
• Business loans
• Education loans

$personalization

What type of loan are you interested in today?""")

    COLLECT_LOAN_DETAILS = Template("""Great! You're interested in a $loan_type loan.

To check your eligibility, I'll need to ask a few questions. This typically takes about 3-5 minutes, and your information is kept secure and confidential.

First, how much would you like to borrow?""")

    COLLECT_INCOME = Template("""Thanks! You're looking for a $$amount $loan_type loan over $term months.

Now, let's look at your financial situation. What is your approximate annual income before taxes?""")

    COLLECT_EMPLOYMENT = Template("""Thank you. And what is your current employment status?

• Employed (full-time or part-time)
• Self-employed
• Retired
• Student
• Currently not employed""")

    COLLECT_CREDIT_SCORE = Template("""$employment_response

Do you know your approximate credit score?

If you're not sure, that's okay - you can estimate or say "I don't know." Credit scores typically range from 300 to 850.

Common ranges:
• Excellent: 750+
• Good: 700-749
• Fair: 650-699
• Needs improvement: Below 650""")

    COLLECT_DEBT = Template("""Almost done! What is your approximate total existing debt?

This includes:
• Credit card balances
• Car loans
• Student loans
• Other loans

An estimate is fine if you don't know the exact amount.""")

    CONFIRM_DETAILS = Template("""Thank you for providing that information. Let me confirm what I have:

**Loan Request:**
• Type: $loan_type
• Amount: $$amount
• Term: $term months

**Your Financial Profile:**
• Annual Income: $$income
• Employment: $employment
• Credit Score: $credit_score
• Existing Debt: $$debt

Is this information correct? (Yes/No)

$disclaimer""")

    ELIGIBILITY_RESULT = Template("""$greeting

**Pre-Qualification Result: $status**

$explanation

**Assessment Summary:**
$factors_summary

$offer_details

**Recommended Next Steps:**
$next_steps

---
$disclaimers""")

    HANDOFF_TO_HUMAN = Template("""I understand you'd like to speak with a loan specialist.

$reason

Here are your options:
1. **Schedule a callback** - A specialist will call you at your preferred time
2. **Live chat** - Connect with a specialist now (available $hours)
3. **Visit a branch** - Find your nearest location

Which would you prefer?""")

    CLARIFICATION_REQUEST = Template("""I want to make sure I understand correctly.

$context

Could you please clarify: $question""")

    ERROR_RECOVERY = Template("""I apologize, but I'm having trouble processing that information.

$specific_issue

Could you please $recovery_action?

If you continue to experience issues, I can connect you with a human representative.""")

    # Compliance templates
    DISCLAIMERS = {
        "pre_qualification": (
            "This pre-qualification is not a commitment to lend. "
            "Final approval is subject to verification of the information provided, "
            "satisfactory appraisal (if applicable), and other underwriting requirements."
        ),
        "rate_estimate": (
            "Interest rates shown are estimates based on the information provided. "
            "Your actual rate may differ based on additional factors including credit history, "
            "loan-to-value ratio, and market conditions at time of application."
        ),
        "privacy": (
            "Your information is protected and will only be used for loan pre-qualification purposes. "
            "See our Privacy Policy for details."
        ),
        "not_advice": (
            "This information is for educational purposes only and should not be considered "
            "financial advice. Please consult with a qualified financial advisor for personalized guidance."
        )
    }

    @classmethod
    def get_greeting(cls, returning_user: bool = False, user_name: Optional[str] = None) -> str:
        """Generate personalized greeting."""
        if returning_user and user_name:
            personalization = f"Welcome back, {user_name}! Would you like to continue where you left off?"
        elif user_name:
            personalization = f"Nice to meet you, {user_name}!"
        else:
            personalization = "Let's find the right loan option for you."

        return cls.GREETING.substitute(personalization=personalization)

    @classmethod
    def get_eligibility_result(
        cls,
        status: str,
        explanation: str,
        factors: list,
        offer_details: Optional[str],
        next_steps: list
    ) -> str:
        """Generate eligibility result message."""
        greeting_map = {
            "eligible": "Congratulations!",
            "conditionally_eligible": "Good news!",
            "needs_review": "Thank you for your patience.",
            "not_eligible": "Thank you for your interest."
        }

        factors_summary = "\n".join(f"• {f['name']}: {f['message']}" for f in factors)
        next_steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(next_steps))

        disclaimers = "\n".join([
            f"*{cls.DISCLAIMERS['pre_qualification']}*",
            f"*{cls.DISCLAIMERS['rate_estimate']}*"
        ])

        return cls.ELIGIBILITY_RESULT.substitute(
            greeting=greeting_map.get(status, ""),
            status=status.replace("_", " ").title(),
            explanation=explanation,
            factors_summary=factors_summary,
            offer_details=offer_details or "",
            next_steps=next_steps_text,
            disclaimers=disclaimers
        )

    @classmethod
    def get_disclaimer(cls, disclaimer_type: str) -> str:
        """Get specific disclaimer text."""
        return cls.DISCLAIMERS.get(disclaimer_type, "")

    @classmethod
    def format_currency(cls, amount: float) -> str:
        """Format amount as currency."""
        return f"${amount:,.2f}"

    @classmethod
    def format_percentage(cls, rate: float) -> str:
        """Format rate as percentage."""
        return f"{rate:.2%}"


class ConversationFlowPrompts:
    """Prompts for managing conversation flow with the LLM."""

    INTENT_CLASSIFICATION = Template("""Classify the user's intent from this message:

Message: "$message"

Possible intents:
- loan_inquiry: Asking about loan types or options
- amount_provided: Providing a loan amount
- income_provided: Providing income information
- employment_provided: Providing employment status
- credit_score_provided: Providing credit score
- debt_provided: Providing debt information
- confirmation: Confirming information (yes/correct)
- correction: Correcting information (no/wrong)
- question: Asking a question
- objection: Expressing concern or hesitation
- handoff_request: Requesting human assistance
- out_of_scope: Message unrelated to loan pre-qualification

Respond with only the intent name.""")

    ENTITY_EXTRACTION = Template("""Extract entities from this message in the context of a loan application:

Message: "$message"
Current step: $current_step

Extract these entities if present:
- loan_type: (personal/home/auto/business/education)
- amount: (numeric dollar amount)
- term_months: (loan term in months)
- annual_income: (numeric dollar amount)
- employment_status: (employed/self_employed/unemployed/retired/student)
- credit_score: (numeric 300-850)
- existing_debt: (numeric dollar amount)

Return as JSON. Use null for entities not found.""")

    RESPONSE_GENERATION = Template("""Generate a response for this conversation state:

Current step: $current_step
Collected data: $collected_data
Missing fields: $missing_fields
User message: "$user_message"
Detected intent: $intent

Requirements:
- Keep response under 100 words
- Ask for ONE piece of missing information at a time
- Acknowledge what the user provided
- Be conversational and natural
- Include brief explanation of why information is needed if appropriate

Generate the response:""")

    VALIDATION_CHECK = Template("""Validate this value for a loan application:

Field: $field_name
Value: $value
Expected type: $expected_type
Constraints: $constraints

Is this value valid? If not, explain why in simple terms suitable for a customer.

Respond in JSON format:
{
    "valid": true/false,
    "message": "explanation if invalid"
}""")
