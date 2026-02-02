"""
Tests for the Eligibility Engine
"""

import pytest
from decimal import Decimal
from datetime import date

import sys
sys.path.insert(0, '../backend')

from backend.app.models import (
    LoanType,
    EmploymentStatus,
    EligibilityStatus,
    ApplicantInfo,
    FinancialInfo,
    LoanRequest,
    LoanApplication
)
from backend.app.services.eligibility_engine import EligibilityEngine


@pytest.fixture
def engine():
    """Create eligibility engine instance."""
    return EligibilityEngine()


@pytest.fixture
def base_application():
    """Create a base loan application for testing."""
    return LoanApplication(
        session_id="test-session-001",
        applicant=ApplicantInfo(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1985, 6, 15),
            email="john@example.com"
        ),
        financial=FinancialInfo(
            annual_income=Decimal("75000"),
            monthly_expenses=Decimal("2500"),
            employment_status=EmploymentStatus.EMPLOYED,
            years_employed=5.0,
            credit_score=720,
            existing_debt=Decimal("15000")
        ),
        loan=LoanRequest(
            loan_type=LoanType.PERSONAL,
            requested_amount=Decimal("25000"),
            loan_term_months=60
        ),
        consent_given=True
    )


class TestEligibilityEngine:
    """Test cases for EligibilityEngine."""

    def test_eligible_application(self, engine, base_application):
        """Test that a strong application is approved."""
        result = engine.evaluate(base_application)

        assert result.status == EligibilityStatus.ELIGIBLE
        assert result.overall_score >= 70
        assert result.approved_amount is not None
        assert result.estimated_rate is not None

    def test_low_credit_score_rejection(self, engine, base_application):
        """Test rejection for low credit score."""
        base_application.financial.credit_score = 500
        result = engine.evaluate(base_application)

        assert result.status in [
            EligibilityStatus.NOT_ELIGIBLE,
            EligibilityStatus.NEEDS_REVIEW
        ]

        # Check that credit score factor failed
        credit_factor = next(
            f for f in result.factors if f.name == "Credit Score"
        )
        assert credit_factor.status == "fail"

    def test_high_dti_rejection(self, engine, base_application):
        """Test handling of high debt-to-income ratio."""
        base_application.financial.existing_debt = Decimal("100000")
        result = engine.evaluate(base_application)

        dti_factor = next(
            f for f in result.factors if f.name == "Debt-to-Income Ratio"
        )
        assert dti_factor.status in ["fail", "warning"]

    def test_unemployed_rejection(self, engine, base_application):
        """Test handling of unemployed applicant."""
        base_application.financial.employment_status = EmploymentStatus.UNEMPLOYED
        result = engine.evaluate(base_application)

        emp_factor = next(
            f for f in result.factors if f.name == "Employment"
        )
        assert emp_factor.status == "fail"

    def test_loan_amount_within_limits(self, engine, base_application):
        """Test that loan amount within limits passes."""
        base_application.loan.requested_amount = Decimal("10000")
        result = engine.evaluate(base_application)

        amount_factor = next(
            f for f in result.factors if f.name == "Loan Amount"
        )
        assert amount_factor.status == "pass"

    def test_loan_amount_exceeds_limits(self, engine, base_application):
        """Test that excessive loan amount fails."""
        base_application.loan.requested_amount = Decimal("100000")  # Over $50k limit
        result = engine.evaluate(base_application)

        amount_factor = next(
            f for f in result.factors if f.name == "Loan Amount"
        )
        assert amount_factor.status == "fail"

    def test_home_loan_criteria(self, engine, base_application):
        """Test home loan specific criteria."""
        base_application.loan.loan_type = LoanType.HOME
        base_application.loan.requested_amount = Decimal("300000")
        base_application.loan.collateral_value = Decimal("350000")
        base_application.loan.down_payment = Decimal("50000")
        base_application.financial.credit_score = 680

        result = engine.evaluate(base_application)

        # Should check LTV factor for home loans
        ltv_factors = [f for f in result.factors if f.name == "Loan-to-Value"]
        assert len(ltv_factors) > 0

    def test_rate_tiers(self, engine, base_application):
        """Test that rate varies with credit score."""
        # Excellent credit
        base_application.financial.credit_score = 800
        result_excellent = engine.evaluate(base_application)

        # Fair credit
        base_application.financial.credit_score = 650
        result_fair = engine.evaluate(base_application)

        # Better credit should get lower rate
        if result_excellent.estimated_rate and result_fair.estimated_rate:
            assert result_excellent.estimated_rate < result_fair.estimated_rate

    def test_monthly_payment_calculation(self, engine, base_application):
        """Test monthly payment calculation."""
        result = engine.evaluate(base_application)

        if result.approved_amount and result.estimated_rate:
            assert result.estimated_monthly_payment is not None
            assert result.estimated_monthly_payment > 0

    def test_next_steps_generated(self, engine, base_application):
        """Test that next steps are always generated."""
        result = engine.evaluate(base_application)
        assert len(result.next_steps) > 0

    def test_disclaimers_included(self, engine, base_application):
        """Test that disclaimers are always included."""
        result = engine.evaluate(base_application)
        assert len(result.disclaimers) > 0

    def test_human_review_flag(self, engine, base_application):
        """Test human review flag for edge cases."""
        # Missing credit score should trigger review
        base_application.financial.credit_score = None
        result = engine.evaluate(base_application)

        # Should have warning for missing credit score
        credit_factor = next(
            f for f in result.factors if f.name == "Credit Score"
        )
        assert credit_factor.status == "warning"

    def test_conditionally_eligible(self, engine, base_application):
        """Test conditionally eligible status."""
        # Borderline application
        base_application.financial.credit_score = 650
        base_application.financial.years_employed = 1.0

        result = engine.evaluate(base_application)

        # Should be eligible or conditionally eligible (not rejected)
        assert result.status in [
            EligibilityStatus.ELIGIBLE,
            EligibilityStatus.CONDITIONALLY_ELIGIBLE,
            EligibilityStatus.NEEDS_REVIEW
        ]


class TestEligibilityScoring:
    """Test scoring calculations."""

    def test_perfect_score_application(self, engine, base_application):
        """Test that perfect application gets high score."""
        base_application.financial.credit_score = 800
        base_application.financial.annual_income = Decimal("150000")
        base_application.financial.existing_debt = Decimal("0")
        base_application.financial.years_employed = 10.0

        result = engine.evaluate(base_application)
        assert result.overall_score >= 90

    def test_score_reflects_factors(self, engine, base_application):
        """Test that score reflects individual factors."""
        result = engine.evaluate(base_application)

        # Count passes and fails
        passes = sum(1 for f in result.factors if f.status == "pass")
        fails = sum(1 for f in result.factors if f.status == "fail")

        # More passes should mean higher score
        if fails == 0:
            assert result.overall_score >= 70
        elif fails >= 2:
            assert result.overall_score < 50


class TestLoanTypeSpecificCriteria:
    """Test loan-type specific criteria."""

    def test_business_loan_higher_requirements(self, engine, base_application):
        """Test that business loans have stricter requirements."""
        base_application.loan.loan_type = LoanType.BUSINESS
        base_application.loan.requested_amount = Decimal("100000")
        base_application.financial.credit_score = 650  # Below 680 minimum

        result = engine.evaluate(base_application)

        credit_factor = next(
            f for f in result.factors if f.name == "Credit Score"
        )
        assert credit_factor.status == "fail"

    def test_education_loan_lower_requirements(self, engine, base_application):
        """Test that education loans have lower requirements."""
        base_application.loan.loan_type = LoanType.EDUCATION
        base_application.financial.credit_score = 600

        result = engine.evaluate(base_application)

        credit_factor = next(
            f for f in result.factors if f.name == "Credit Score"
        )
        assert credit_factor.status == "pass"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
