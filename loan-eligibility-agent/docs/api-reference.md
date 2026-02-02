# API Reference

## Overview

The Loan Eligibility Agent API provides endpoints for loan pre-qualification assessment, conversational interactions, and Dialogflow CX webhook fulfillment.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

For production deployments, API authentication is required via API key:

```
Authorization: Bearer <API_KEY>
```

## Endpoints

---

## Eligibility Assessment

### Full Eligibility Check

Performs a comprehensive loan eligibility assessment.

**POST** `/eligibility/check`

#### Request Body

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1985-06-15",
  "email": "john.doe@example.com",
  "annual_income": 75000,
  "monthly_expenses": 2500,
  "employment_status": "employed",
  "employer_name": "Tech Corp",
  "years_employed": 5,
  "credit_score": 720,
  "existing_debt": 15000,
  "loan_type": "personal",
  "requested_amount": 25000,
  "loan_purpose": "Debt consolidation",
  "loan_term_months": 60,
  "collateral_value": null,
  "down_payment": null,
  "consent_given": true
}
```

#### Response

```json
{
  "session_id": "abc123-def456",
  "status": "eligible",
  "loan_type": "personal",
  "requested_amount": 25000,
  "approved_amount": 25000,
  "estimated_rate": 0.0999,
  "estimated_monthly_payment": 531.18,
  "overall_score": 85.5,
  "explanation": "Based on your information, you pre-qualify for a personal loan...",
  "factors": [
    {
      "name": "Credit Score",
      "status": "pass",
      "message": "Credit score of 720 meets minimum requirement of 620",
      "weight": 0.25,
      "details": {
        "score": 720,
        "minimum": 620,
        "margin": 100
      }
    }
  ],
  "next_steps": [
    "Complete full loan application",
    "Gather required documentation"
  ],
  "disclaimers": [
    "This is a pre-qualification estimate and not a final loan offer."
  ],
  "requires_human_review": false
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Successful assessment |
| 400 | Invalid request (missing consent, validation error) |
| 500 | Server error |

---

### Quick Eligibility Check

Performs a rapid eligibility estimate with minimal information.

**POST** `/eligibility/quick-check`

#### Request Body

```json
{
  "loan_type": "personal",
  "requested_amount": 20000,
  "annual_income": 60000,
  "credit_score": 700,
  "existing_debt": 5000
}
```

#### Response

```json
{
  "likely_eligible": true,
  "confidence": "high",
  "estimated_rate_range": "9.99% - 12.99%",
  "key_factors": [
    "Good credit score",
    "Low debt-to-income ratio",
    "Conservative loan amount relative to income"
  ],
  "recommendation": "You appear to be a strong candidate. We recommend completing the full application."
}
```

---

### Get Loan Types

Returns available loan types and their basic criteria.

**GET** `/eligibility/loan-types`

#### Response

```json
{
  "loan_types": [
    {
      "type": "personal",
      "name": "Personal Loan",
      "description": "Unsecured loans for various personal needs",
      "min_amount": 1000,
      "max_amount": 50000,
      "term_range": "12-84 months",
      "min_credit_score": 620
    }
  ]
}
```

---

## Conversation Management

### Start Conversation

Initiates a new pre-qualification conversation session.

**POST** `/conversation/start`

#### Response

```json
{
  "session_id": "uuid-session-id",
  "message": "Welcome to our loan pre-qualification service...",
  "current_step": "collect_loan_type"
}
```

---

### Send Message

Sends a message within an existing conversation.

**POST** `/conversation/message`

#### Request Body

```json
{
  "session_id": "uuid-session-id",
  "message": "I'm interested in a personal loan"
}
```

#### Response

```json
{
  "session_id": "uuid-session-id",
  "response": "Great choice! How much would you like to borrow?",
  "current_step": "collect_amount",
  "collected_data": {
    "loan_type": "personal"
  },
  "missing_fields": ["requested_amount", "annual_income", "employment_status"],
  "conversation_complete": false
}
```

---

### Get Conversation History

Retrieves the full conversation history for a session.

**GET** `/conversation/history/{session_id}`

#### Response

```json
{
  "session_id": "uuid-session-id",
  "messages": [
    {
      "role": "assistant",
      "content": "Welcome to our loan pre-qualification service...",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "user",
      "content": "I need a personal loan",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ],
  "current_step": "collect_amount",
  "started_at": "2024-01-15T10:30:00Z",
  "last_activity": "2024-01-15T10:30:15Z"
}
```

---

### Request Human Handoff

Requests transfer to a human agent.

**POST** `/conversation/handoff/{session_id}`

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| reason | string | Optional reason for handoff |

#### Response

```json
{
  "message": "Handoff request received",
  "session_id": "uuid-session-id",
  "handoff_options": [
    {
      "type": "callback",
      "description": "Schedule a callback from a loan specialist",
      "availability": "Within 24 hours"
    },
    {
      "type": "live_chat",
      "description": "Connect with an agent now",
      "availability": "Mon-Fri 8am-8pm EST"
    }
  ],
  "conversation_summary": {
    "current_step": "collect_income",
    "data_collected": ["loan_type", "requested_amount"],
    "message_count": 5
  }
}
```

---

## Webhook (Dialogflow CX)

### Dialogflow Fulfillment

Handles webhook fulfillment requests from Dialogflow CX.

**POST** `/webhook/dialogflow`

#### Request Body

Standard Dialogflow CX webhook request format.

#### Fulfillment Tags

| Tag | Description |
|-----|-------------|
| `validate_loan_amount` | Validates requested loan amount |
| `validate_income` | Validates income information |
| `validate_credit_score` | Validates credit score |
| `check_eligibility` | Performs eligibility assessment |
| `explain_rejection` | Generates rejection explanation |
| `calculate_payment` | Calculates estimated payment |
| `human_handoff` | Initiates human agent transfer |

---

## Health Checks

### Basic Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "service": "Loan Eligibility Agent",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Detailed Health Check

**GET** `/health/detailed`

```json
{
  "status": "healthy",
  "service": "Loan Eligibility Agent",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "llm_service": {
      "status": "healthy",
      "provider": "OpenAIProvider"
    },
    "dialogflow": {
      "status": "healthy",
      "project": "my-gcp-project",
      "agent": "agent-id"
    }
  }
}
```

---

## Data Models

### LoanType

```
personal | home | auto | business | education
```

### EmploymentStatus

```
employed | self_employed | unemployed | retired | student
```

### EligibilityStatus

```
eligible | conditionally_eligible | not_eligible | needs_review
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Human-readable error message"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Session not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

Default limits:
- 100 requests per minute per IP
- 1000 requests per hour per API key

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673784000
```
