"""Data models for the loan eligibility agent."""

from .loan_application import (
    LoanType,
    EmploymentStatus,
    EligibilityStatus,
    ApplicantInfo,
    FinancialInfo,
    LoanRequest,
    LoanApplication,
    EligibilityFactor,
    EligibilityResult,
    ConversationState
)

__all__ = [
    "LoanType",
    "EmploymentStatus",
    "EligibilityStatus",
    "ApplicantInfo",
    "FinancialInfo",
    "LoanRequest",
    "LoanApplication",
    "EligibilityFactor",
    "EligibilityResult",
    "ConversationState"
]
