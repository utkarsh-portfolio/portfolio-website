"""
Loan Eligibility Engine
Core business logic for determining loan eligibility based on financial factors.
"""

from decimal import Decimal
from typing import List, Tuple, Optional
import logging

from ..models import (
    LoanApplication,
    LoanType,
    EmploymentStatus,
    EligibilityStatus,
    EligibilityFactor,
    EligibilityResult
)

logger = logging.getLogger(__name__)


class EligibilityEngine:
    """
    Evaluates loan applications and determines eligibility.

    This engine implements industry-standard lending criteria including:
    - Debt-to-income ratio analysis
    - Credit score evaluation
    - Employment stability assessment
    - Loan-to-value calculations
    """

    # Eligibility thresholds by loan type
    LOAN_CRITERIA = {
        LoanType.PERSONAL: {
            "min_credit_score": 620,
            "max_dti": 0.43,
            "min_income": 20000,
            "max_amount": 50000,
            "min_employment_years": 0.5,
        },
        LoanType.HOME: {
            "min_credit_score": 640,
            "max_dti": 0.43,
            "min_income": 40000,
            "max_amount": 750000,
            "min_employment_years": 2,
            "max_ltv": 0.97,  # With PMI
        },
        LoanType.AUTO: {
            "min_credit_score": 600,
            "max_dti": 0.50,
            "min_income": 18000,
            "max_amount": 100000,
            "min_employment_years": 0.5,
            "max_ltv": 1.25,
        },
        LoanType.BUSINESS: {
            "min_credit_score": 680,
            "max_dti": 0.40,
            "min_income": 50000,
            "max_amount": 500000,
            "min_employment_years": 2,
        },
        LoanType.EDUCATION: {
            "min_credit_score": 580,
            "max_dti": 0.50,
            "min_income": 0,  # Can have co-signer
            "max_amount": 200000,
            "min_employment_years": 0,
        },
    }

    # Interest rate tiers based on credit score
    RATE_TIERS = {
        (800, 850): 0.0599,
        (750, 799): 0.0749,
        (700, 749): 0.0999,
        (650, 699): 0.1299,
        (600, 649): 0.1599,
        (550, 599): 0.1999,
        (300, 549): 0.2499,
    }

    def __init__(self):
        self.disclaimers = [
            "This is a pre-qualification estimate and not a final loan offer.",
            "Final approval is subject to verification of information provided.",
            "Interest rates and terms may vary based on additional underwriting factors.",
            "This assessment does not guarantee loan approval.",
        ]

    def evaluate(self, application: LoanApplication) -> EligibilityResult:
        """
        Evaluate a loan application and return eligibility result.

        Args:
            application: Complete loan application with all required information

        Returns:
            EligibilityResult with detailed assessment
        """
        logger.info(f"Evaluating application for session: {application.session_id}")

        factors: List[EligibilityFactor] = []
        loan_type = application.loan.loan_type
        criteria = self.LOAN_CRITERIA[loan_type]

        # Run all eligibility checks
        factors.append(self._check_credit_score(application, criteria))
        factors.append(self._check_income(application, criteria))
        factors.append(self._check_dti(application, criteria))
        factors.append(self._check_employment(application, criteria))
        factors.append(self._check_loan_amount(application, criteria))

        if loan_type in [LoanType.HOME, LoanType.AUTO]:
            factors.append(self._check_ltv(application, criteria))

        # Calculate overall score and status
        overall_score = self._calculate_score(factors)
        status = self._determine_status(factors, overall_score)

        # Calculate approved amount and rate
        approved_amount, estimated_rate = self._calculate_offer(
            application, factors, status
        )

        # Calculate monthly payment if approved
        monthly_payment = None
        if approved_amount and estimated_rate:
            monthly_payment = self._calculate_monthly_payment(
                approved_amount,
                estimated_rate,
                application.loan.loan_term_months
            )

        # Determine if human review is needed
        requires_human = self._needs_human_review(factors, status)

        # Generate next steps
        next_steps = self._generate_next_steps(status, factors, requires_human)

        result = EligibilityResult(
            session_id=application.session_id,
            status=status,
            loan_type=loan_type,
            requested_amount=application.loan.requested_amount,
            approved_amount=approved_amount,
            estimated_rate=estimated_rate,
            estimated_monthly_payment=monthly_payment,
            factors=factors,
            overall_score=overall_score,
            explanation="",  # Will be filled by LLM service
            next_steps=next_steps,
            disclaimers=self.disclaimers,
            requires_human_review=requires_human
        )

        logger.info(
            f"Eligibility result for {application.session_id}: "
            f"status={status}, score={overall_score}"
        )

        return result

    def _check_credit_score(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check if credit score meets minimum requirements."""
        credit_score = application.financial.credit_score
        min_score = criteria["min_credit_score"]

        if credit_score is None:
            return EligibilityFactor(
                name="Credit Score",
                status="warning",
                message="Credit score not provided. Will need to be verified.",
                weight=0.25,
                details={"provided": False}
            )

        if credit_score >= min_score + 100:
            status = "pass"
            message = f"Excellent credit score of {credit_score}"
        elif credit_score >= min_score:
            status = "pass"
            message = f"Credit score of {credit_score} meets minimum requirement of {min_score}"
        else:
            status = "fail"
            message = f"Credit score of {credit_score} is below minimum of {min_score}"

        return EligibilityFactor(
            name="Credit Score",
            status=status,
            message=message,
            weight=0.25,
            details={
                "score": credit_score,
                "minimum": min_score,
                "margin": credit_score - min_score
            }
        )

    def _check_income(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check if income meets minimum requirements."""
        annual_income = float(application.financial.annual_income)
        min_income = criteria["min_income"]

        if annual_income >= min_income * 2:
            status = "pass"
            message = f"Strong annual income of ${annual_income:,.0f}"
        elif annual_income >= min_income:
            status = "pass"
            message = f"Annual income of ${annual_income:,.0f} meets requirement"
        else:
            status = "fail"
            message = f"Annual income of ${annual_income:,.0f} is below minimum of ${min_income:,.0f}"

        return EligibilityFactor(
            name="Income",
            status=status,
            message=message,
            weight=0.20,
            details={
                "annual_income": annual_income,
                "minimum": min_income
            }
        )

    def _check_dti(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check debt-to-income ratio."""
        annual_income = float(application.financial.annual_income)
        existing_debt = float(application.financial.existing_debt)
        requested_amount = float(application.loan.requested_amount)
        term_months = application.loan.loan_term_months

        # Estimate new monthly payment (simple calculation)
        estimated_rate = 0.10  # Assume 10% for DTI calculation
        monthly_payment = self._calculate_monthly_payment(
            Decimal(str(requested_amount)),
            estimated_rate,
            term_months
        )

        monthly_income = annual_income / 12
        total_monthly_debt = (existing_debt / 12) + float(monthly_payment)
        dti = total_monthly_debt / monthly_income if monthly_income > 0 else float('inf')

        max_dti = criteria["max_dti"]

        if dti <= max_dti * 0.7:
            status = "pass"
            message = f"Excellent debt-to-income ratio of {dti:.1%}"
        elif dti <= max_dti:
            status = "pass"
            message = f"Debt-to-income ratio of {dti:.1%} is acceptable"
        else:
            status = "fail"
            message = f"Debt-to-income ratio of {dti:.1%} exceeds maximum of {max_dti:.1%}"

        return EligibilityFactor(
            name="Debt-to-Income Ratio",
            status=status,
            message=message,
            weight=0.25,
            details={
                "dti": round(dti, 4),
                "maximum": max_dti,
                "monthly_income": round(monthly_income, 2),
                "total_monthly_debt": round(total_monthly_debt, 2)
            }
        )

    def _check_employment(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check employment stability."""
        emp_status = application.financial.employment_status
        years_employed = application.financial.years_employed or 0
        min_years = criteria["min_employment_years"]

        # Handle different employment statuses
        if emp_status == EmploymentStatus.UNEMPLOYED:
            return EligibilityFactor(
                name="Employment",
                status="fail",
                message="Currently unemployed - stable income source required",
                weight=0.15,
                details={"status": emp_status.value, "years": years_employed}
            )

        if emp_status == EmploymentStatus.RETIRED:
            return EligibilityFactor(
                name="Employment",
                status="pass",
                message="Retired - will verify retirement income sources",
                weight=0.15,
                details={"status": emp_status.value}
            )

        if years_employed >= min_years:
            status = "pass"
            message = f"Employed for {years_employed:.1f} years (minimum: {min_years})"
        else:
            status = "warning"
            message = f"Employment history of {years_employed:.1f} years is below preferred {min_years} years"

        return EligibilityFactor(
            name="Employment",
            status=status,
            message=message,
            weight=0.15,
            details={
                "status": emp_status.value,
                "years": years_employed,
                "minimum_years": min_years
            }
        )

    def _check_loan_amount(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check if requested loan amount is within limits."""
        requested = float(application.loan.requested_amount)
        max_amount = criteria["max_amount"]

        if requested <= max_amount:
            status = "pass"
            message = f"Requested amount of ${requested:,.0f} is within program limits"
        else:
            status = "fail"
            message = f"Requested amount of ${requested:,.0f} exceeds maximum of ${max_amount:,.0f}"

        return EligibilityFactor(
            name="Loan Amount",
            status=status,
            message=message,
            weight=0.10,
            details={
                "requested": requested,
                "maximum": max_amount
            }
        )

    def _check_ltv(
        self,
        application: LoanApplication,
        criteria: dict
    ) -> EligibilityFactor:
        """Check loan-to-value ratio for secured loans."""
        requested = float(application.loan.requested_amount)
        collateral = float(application.loan.collateral_value or 0)
        down_payment = float(application.loan.down_payment or 0)

        if collateral == 0:
            return EligibilityFactor(
                name="Loan-to-Value",
                status="warning",
                message="Collateral value not provided - will need appraisal",
                weight=0.05,
                details={"provided": False}
            )

        ltv = (requested - down_payment) / collateral
        max_ltv = criteria.get("max_ltv", 1.0)

        if ltv <= max_ltv * 0.8:
            status = "pass"
            message = f"Excellent loan-to-value ratio of {ltv:.1%}"
        elif ltv <= max_ltv:
            status = "pass"
            message = f"Loan-to-value ratio of {ltv:.1%} is acceptable"
        else:
            status = "fail"
            message = f"Loan-to-value ratio of {ltv:.1%} exceeds maximum of {max_ltv:.1%}"

        return EligibilityFactor(
            name="Loan-to-Value",
            status=status,
            message=message,
            weight=0.05,
            details={
                "ltv": round(ltv, 4),
                "maximum": max_ltv,
                "collateral_value": collateral,
                "down_payment": down_payment
            }
        )

    def _calculate_score(self, factors: List[EligibilityFactor]) -> float:
        """Calculate overall eligibility score from factors."""
        total_weight = sum(f.weight for f in factors)
        weighted_score = 0

        for factor in factors:
            if factor.status == "pass":
                factor_score = 100
            elif factor.status == "warning":
                factor_score = 60
            else:  # fail
                factor_score = 0

            weighted_score += factor_score * factor.weight

        return round(weighted_score / total_weight if total_weight > 0 else 0, 1)

    def _determine_status(
        self,
        factors: List[EligibilityFactor],
        score: float
    ) -> EligibilityStatus:
        """Determine eligibility status based on factors and score."""
        fail_count = sum(1 for f in factors if f.status == "fail")
        warning_count = sum(1 for f in factors if f.status == "warning")

        # Critical failures
        critical_factors = ["Credit Score", "Income", "Debt-to-Income Ratio"]
        critical_fails = [
            f for f in factors
            if f.name in critical_factors and f.status == "fail"
        ]

        if len(critical_fails) >= 2:
            return EligibilityStatus.NOT_ELIGIBLE

        if fail_count >= 2:
            return EligibilityStatus.NOT_ELIGIBLE

        if score >= 80 and fail_count == 0:
            return EligibilityStatus.ELIGIBLE

        if score >= 50:
            return EligibilityStatus.CONDITIONALLY_ELIGIBLE

        if warning_count >= 2 or fail_count == 1:
            return EligibilityStatus.NEEDS_REVIEW

        return EligibilityStatus.NOT_ELIGIBLE

    def _calculate_offer(
        self,
        application: LoanApplication,
        factors: List[EligibilityFactor],
        status: EligibilityStatus
    ) -> Tuple[Optional[Decimal], Optional[float]]:
        """Calculate approved amount and estimated interest rate."""
        if status == EligibilityStatus.NOT_ELIGIBLE:
            return None, None

        requested = application.loan.requested_amount
        credit_score = application.financial.credit_score or 650

        # Determine rate based on credit score
        estimated_rate = 0.15  # Default
        for (low, high), rate in self.RATE_TIERS.items():
            if low <= credit_score <= high:
                estimated_rate = rate
                break

        # Adjust approved amount based on status
        if status == EligibilityStatus.ELIGIBLE:
            approved = requested
        elif status == EligibilityStatus.CONDITIONALLY_ELIGIBLE:
            # May approve reduced amount
            approved = requested * Decimal("0.85")
        else:  # NEEDS_REVIEW
            approved = requested * Decimal("0.75")

        return approved.quantize(Decimal("0.01")), estimated_rate

    def _calculate_monthly_payment(
        self,
        principal: Decimal,
        annual_rate: float,
        term_months: int
    ) -> Decimal:
        """Calculate monthly payment using amortization formula."""
        if annual_rate == 0:
            return principal / term_months

        monthly_rate = annual_rate / 12
        payment = float(principal) * (
            monthly_rate * (1 + monthly_rate) ** term_months
        ) / (
            (1 + monthly_rate) ** term_months - 1
        )
        return Decimal(str(round(payment, 2)))

    def _needs_human_review(
        self,
        factors: List[EligibilityFactor],
        status: EligibilityStatus
    ) -> bool:
        """Determine if application needs human review."""
        if status == EligibilityStatus.NEEDS_REVIEW:
            return True

        # Check for edge cases
        warning_count = sum(1 for f in factors if f.status == "warning")
        if warning_count >= 2:
            return True

        # Check for missing information
        for factor in factors:
            if factor.details and factor.details.get("provided") is False:
                return True

        return False

    def _generate_next_steps(
        self,
        status: EligibilityStatus,
        factors: List[EligibilityFactor],
        requires_human: bool
    ) -> List[str]:
        """Generate recommended next steps based on assessment."""
        steps = []

        if status == EligibilityStatus.ELIGIBLE:
            steps.append("Complete full loan application")
            steps.append("Gather required documentation (ID, income verification)")
            steps.append("Schedule appointment with loan officer")

        elif status == EligibilityStatus.CONDITIONALLY_ELIGIBLE:
            steps.append("Review conditions for approval")
            # Add specific recommendations based on weak factors
            for factor in factors:
                if factor.status == "warning":
                    if factor.name == "Credit Score":
                        steps.append("Consider improving credit score before applying")
                    elif factor.name == "Employment":
                        steps.append("Provide additional employment documentation")
            steps.append("Speak with a loan specialist about your options")

        elif status == EligibilityStatus.NEEDS_REVIEW:
            steps.append("Your application requires additional review")
            steps.append("A loan specialist will contact you within 24-48 hours")
            steps.append("Prepare additional documentation if requested")

        else:  # NOT_ELIGIBLE
            steps.append("Review factors affecting your eligibility")
            # Specific improvement suggestions
            for factor in factors:
                if factor.status == "fail":
                    if factor.name == "Credit Score":
                        steps.append("Work on improving your credit score")
                    elif factor.name == "Debt-to-Income Ratio":
                        steps.append("Consider paying down existing debt")
                    elif factor.name == "Income":
                        steps.append("Consider a co-signer or wait for income increase")
            steps.append("Explore alternative lending options")
            steps.append("Schedule a consultation for personalized guidance")

        if requires_human:
            steps.append("Would you like to speak with a human representative?")

        return steps
