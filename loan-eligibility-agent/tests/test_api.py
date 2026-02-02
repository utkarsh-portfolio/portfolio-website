"""
Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date

import sys
sys.path.insert(0, '../backend')

from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness probe."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check(self, client):
        """Test liveness probe."""
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestEligibilityEndpoints:
    """Test eligibility API endpoints."""

    def test_get_loan_types(self, client):
        """Test getting available loan types."""
        response = client.get("/api/v1/eligibility/loan-types")
        assert response.status_code == 200

        data = response.json()
        assert "loan_types" in data
        assert len(data["loan_types"]) > 0

        # Check loan type structure
        loan_type = data["loan_types"][0]
        assert "type" in loan_type
        assert "name" in loan_type
        assert "min_amount" in loan_type
        assert "max_amount" in loan_type

    def test_quick_check_eligible(self, client):
        """Test quick eligibility check for eligible applicant."""
        response = client.post(
            "/api/v1/eligibility/quick-check",
            json={
                "loan_type": "personal",
                "requested_amount": 20000,
                "annual_income": 80000,
                "credit_score": 750,
                "existing_debt": 5000
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "likely_eligible" in data
        assert "confidence" in data
        assert "key_factors" in data
        assert data["likely_eligible"] is True

    def test_quick_check_not_eligible(self, client):
        """Test quick check for unlikely eligible applicant."""
        response = client.post(
            "/api/v1/eligibility/quick-check",
            json={
                "loan_type": "personal",
                "requested_amount": 50000,
                "annual_income": 30000,
                "credit_score": 520,
                "existing_debt": 40000
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["likely_eligible"] is False

    def test_full_eligibility_check(self, client):
        """Test full eligibility assessment."""
        response = client.post(
            "/api/v1/eligibility/check",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15",
                "email": "john@example.com",
                "annual_income": 75000,
                "monthly_expenses": 2500,
                "employment_status": "employed",
                "years_employed": 5,
                "credit_score": 720,
                "existing_debt": 15000,
                "loan_type": "personal",
                "requested_amount": 25000,
                "loan_term_months": 60,
                "consent_given": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert "factors" in data
        assert "next_steps" in data
        assert "disclaimers" in data

    def test_eligibility_check_requires_consent(self, client):
        """Test that consent is required."""
        response = client.post(
            "/api/v1/eligibility/check",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15",
                "annual_income": 75000,
                "employment_status": "employed",
                "loan_type": "personal",
                "requested_amount": 25000,
                "loan_term_months": 60,
                "consent_given": False  # No consent
            }
        )
        assert response.status_code == 400

    def test_eligibility_check_validation(self, client):
        """Test input validation."""
        # Missing required field
        response = client.post(
            "/api/v1/eligibility/check",
            json={
                "first_name": "John",
                # Missing last_name
                "date_of_birth": "1985-06-15",
                "annual_income": 75000,
                "employment_status": "employed",
                "loan_type": "personal",
                "requested_amount": 25000,
                "loan_term_months": 60,
                "consent_given": True
            }
        )
        assert response.status_code == 422  # Validation error


class TestConversationEndpoints:
    """Test conversation API endpoints."""

    def test_start_conversation(self, client):
        """Test starting a new conversation."""
        response = client.post("/api/v1/conversation/start")
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert "current_step" in data

    def test_send_message(self, client):
        """Test sending a message in conversation."""
        # Start conversation first
        start_response = client.post("/api/v1/conversation/start")
        session_id = start_response.json()["session_id"]

        # Send message
        response = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": session_id,
                "message": "I want a personal loan"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == session_id
        assert "response" in data
        assert "current_step" in data

    def test_get_conversation_state(self, client):
        """Test getting conversation state."""
        # Start conversation
        start_response = client.post("/api/v1/conversation/start")
        session_id = start_response.json()["session_id"]

        # Get state
        response = client.get(f"/api/v1/conversation/state/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == session_id
        assert "current_step" in data

    def test_invalid_session(self, client):
        """Test handling of invalid session ID."""
        response = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": "nonexistent-session",
                "message": "Hello"
            }
        )
        assert response.status_code == 404

    def test_request_handoff(self, client):
        """Test requesting human handoff."""
        # Start conversation
        start_response = client.post("/api/v1/conversation/start")
        session_id = start_response.json()["session_id"]

        # Request handoff
        response = client.post(
            f"/api/v1/conversation/handoff/{session_id}",
            params={"reason": "user_requested"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "handoff_options" in data
        assert len(data["handoff_options"]) > 0

    def test_end_conversation(self, client):
        """Test ending a conversation."""
        # Start conversation
        start_response = client.post("/api/v1/conversation/start")
        session_id = start_response.json()["session_id"]

        # End conversation
        response = client.delete(f"/api/v1/conversation/session/{session_id}")
        assert response.status_code == 200

        # Try to access ended session
        response = client.get(f"/api/v1/conversation/state/{session_id}")
        assert response.status_code == 404


class TestWebhookEndpoints:
    """Test Dialogflow webhook endpoints."""

    def test_webhook_validate_amount(self, client):
        """Test loan amount validation webhook."""
        response = client.post(
            "/api/v1/webhook/dialogflow",
            json={
                "sessionInfo": {
                    "session": "projects/test/sessions/123",
                    "parameters": {
                        "loan_type": "personal",
                        "loan_amount": 25000
                    }
                },
                "fulfillmentInfo": {
                    "tag": "validate_loan_amount"
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "fulfillmentResponse" in data or "sessionInfo" in data

    def test_webhook_check_eligibility(self, client):
        """Test eligibility check webhook."""
        response = client.post(
            "/api/v1/webhook/dialogflow",
            json={
                "sessionInfo": {
                    "session": "projects/test/sessions/123",
                    "parameters": {
                        "loan_type": "personal",
                        "loan_amount": 25000,
                        "annual_income": 75000,
                        "employment_status": "employed",
                        "credit_score": 720,
                        "existing_debt": 10000
                    }
                },
                "fulfillmentInfo": {
                    "tag": "check_eligibility"
                }
            }
        )
        assert response.status_code == 200


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "documentation" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
