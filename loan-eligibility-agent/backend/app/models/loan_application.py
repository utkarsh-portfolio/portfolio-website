"""
Loan Application Data Models
Defines the structure for loan applications and eligibility assessments.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import date, datetime
from decimal import Decimal


class LoanType(str, Enum):
    """Supported loan types."""
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    BUSINESS = "business"
    EDUCATION = "education"


class EmploymentStatus(str, Enum):
    """Employment status options."""
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class EligibilityStatus(str, Enum):
    """Eligibility decision status."""
    ELIGIBLE = "eligible"
    CONDITIONALLY_ELIGIBLE = "conditionally_eligible"
    NOT_ELIGIBLE = "not_eligible"
    NEEDS_REVIEW = "needs_review"


class ApplicantInfo(BaseModel):
    """Personal information of the loan applicant."""

    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    ssn_last_four: Optional[str] = Field(None, min_length=4, max_length=4)

    @validator("date_of_birth")
    def validate_age(cls, v):
        """Ensure applicant is at least 18 years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Applicant must be at least 18 years old")
        return v


class FinancialInfo(BaseModel):
    """Financial information of the applicant."""

    annual_income: Decimal = Field(..., gt=0, description="Annual gross income")
    monthly_expenses: Decimal = Field(..., ge=0, description="Monthly expenses")
    employment_status: EmploymentStatus
    employer_name: Optional[str] = None
    years_employed: Optional[float] = Field(None, ge=0)
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    existing_debt: Decimal = Field(default=Decimal("0"), ge=0)
    bank_balance: Optional[Decimal] = Field(None, ge=0)

    @property
    def monthly_income(self) -> Decimal:
        """Calculate monthly income from annual."""
        return self.annual_income / 12

    @property
    def debt_to_income_ratio(self) -> float:
        """Calculate DTI ratio."""
        if self.annual_income == 0:
            return float("inf")
        return float(self.existing_debt / self.annual_income)


class LoanRequest(BaseModel):
    """Loan request details."""

    loan_type: LoanType
    requested_amount: Decimal = Field(..., gt=0)
    loan_purpose: Optional[str] = None
    loan_term_months: int = Field(..., gt=0, le=360)
    collateral_value: Optional[Decimal] = Field(None, ge=0)
    down_payment: Optional[Decimal] = Field(None, ge=0)


class LoanApplication(BaseModel):
    """Complete loan application."""

    session_id: str
    applicant: ApplicantInfo
    financial: FinancialInfo
    loan: LoanRequest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    consent_given: bool = False

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class EligibilityFactor(BaseModel):
    """Individual factor in eligibility assessment."""

    name: str
    status: str  # "pass", "warning", "fail"
    message: str
    weight: float = 1.0
    details: Optional[Dict[str, Any]] = None


class EligibilityResult(BaseModel):
    """Result of loan eligibility assessment."""

    session_id: str
    status: EligibilityStatus
    loan_type: LoanType
    requested_amount: Decimal
    approved_amount: Optional[Decimal] = None
    estimated_rate: Optional[float] = None
    estimated_monthly_payment: Optional[Decimal] = None
    factors: List[EligibilityFactor]
    overall_score: float = Field(..., ge=0, le=100)
    explanation: str
    next_steps: List[str]
    disclaimers: List[str]
    requires_human_review: bool = False
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class ConversationState(BaseModel):
    """Tracks the state of an ongoing conversation."""

    session_id: str
    current_step: str = "greeting"
    collected_data: Dict[str, Any] = {}
    missing_fields: List[str] = []
    validation_errors: List[str] = []
    conversation_history: List[Dict[str, str]] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.update_activity()
