# Loan Eligibility Agent

A production-grade conversational AI agent for loan pre-qualification in financial services environments. Built with FastAPI, Dialogflow CX, and LLM integration (Vertex AI/OpenAI).

![Architecture](docs/architecture.png)

## Overview

This project demonstrates the design, development, and deployment of intelligent synthetic agents that power self-service experiences for loan pre-qualification. It showcases skills relevant to Conversational Agent Developer roles in financial services.

### Key Features

- **Conversational AI**: Natural language loan pre-qualification using Dialogflow CX
- **LLM-Powered Explanations**: Human-readable eligibility decisions using Vertex AI or OpenAI
- **RESTful APIs**: Comprehensive API for eligibility assessment and conversation management
- **Compliance Ready**: Built-in disclaimers, audit logging, and regulatory considerations
- **Real-time Monitoring**: Splunk integration for observability and analytics
- **Human Handoff**: Seamless escalation to human agents with context preservation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                   │
├─────────────────┬─────────────────┬─────────────────────────────────────┤
│   Web Chat UI   │   Mobile App    │        Third-party Integrations     │
└────────┬────────┴────────┬────────┴────────────────┬────────────────────┘
         │                 │                          │
         ▼                 ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Gateway (Apigee)                              │
│   • Rate Limiting  • Authentication  • Request Routing  • Analytics     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Conversation   │    │   Eligibility   │    │    Webhook      │
│     Service     │    │     Service     │    │    Service      │
│                 │    │                 │    │                 │
│ • Session Mgmt  │    │ • Rule Engine   │    │ • Dialogflow CX │
│ • Flow Control  │    │ • DTI Calc      │    │   Fulfillment   │
│ • State Machine │    │ • Credit Check  │    │ • Intent Handle │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LLM Service                                     │
│        • Vertex AI (Gemini)  • OpenAI (GPT-4)  • Prompt Engineering     │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                            │
│           • Splunk Dashboards  • Alerts  • Audit Logging                │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Conversational AI | Dialogflow CX |
| LLM | Vertex AI (Gemini), OpenAI (GPT-4) |
| Cloud Platform | Google Cloud Platform |
| API Management | Apigee |
| Monitoring | Splunk |
| Containerization | Docker |

## Project Structure

```
loan-eligibility-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── eligibility.py    # Eligibility check endpoints
│   │   │       ├── conversation.py   # Conversation management
│   │   │       ├── webhook.py        # Dialogflow CX webhooks
│   │   │       └── health.py         # Health checks
│   │   ├── services/
│   │   │   ├── eligibility_engine.py # Core eligibility logic
│   │   │   ├── llm_service.py        # LLM integration
│   │   │   └── conversation_service.py
│   │   ├── models/                   # Pydantic data models
│   │   ├── prompts/                  # LLM prompt templates
│   │   ├── core/                     # Configuration & logging
│   │   └── main.py                   # FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
├── dialogflow/
│   ├── agent.json                    # Agent configuration
│   ├── flows/                        # Conversation flows
│   ├── intents/                      # Intent definitions
│   └── entities/                     # Custom entities
├── frontend/
│   ├── templates/
│   │   └── index.html               # Demo landing page
│   └── static/
│       ├── css/styles.css
│       └── js/chat.js               # Chat widget
├── monitoring/
│   ├── splunk_config.py             # Splunk HEC client
│   └── alerts.json                  # Alert definitions
├── tests/                           # Test suite
└── docs/                            # Documentation
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional)
- Google Cloud Platform account (for Dialogflow CX)
- OpenAI API key or Vertex AI access

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/loan-eligibility-agent.git
   cd loan-eligibility-agent
   ```

2. **Set up virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Demo UI: http://localhost:8000

### Docker Deployment

```bash
docker build -t loan-eligibility-agent ./backend
docker run -p 8000:8000 --env-file .env loan-eligibility-agent
```

## API Endpoints

### Eligibility Assessment

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/eligibility/check` | Full eligibility assessment |
| POST | `/api/v1/eligibility/quick-check` | Quick eligibility estimate |
| GET | `/api/v1/eligibility/loan-types` | Available loan types |

### Conversation Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/conversation/start` | Start new conversation |
| POST | `/api/v1/conversation/message` | Send message |
| GET | `/api/v1/conversation/history/{id}` | Get conversation history |
| POST | `/api/v1/conversation/handoff/{id}` | Request human handoff |

### Webhook

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhook/dialogflow` | Dialogflow CX fulfillment |

## Eligibility Criteria

The agent evaluates applications based on:

| Factor | Weight | Criteria |
|--------|--------|----------|
| Credit Score | 25% | Minimum varies by loan type (580-680) |
| Debt-to-Income | 25% | Maximum 43-50% depending on loan |
| Income | 20% | Minimum varies by loan type |
| Employment | 15% | Stability and duration |
| Loan Amount | 10% | Within program limits |
| LTV Ratio | 5% | For secured loans |

## Loan Types Supported

- **Personal Loans**: $1,000 - $50,000
- **Home Loans**: $50,000 - $750,000
- **Auto Loans**: $5,000 - $100,000
- **Business Loans**: $10,000 - $500,000
- **Education Loans**: $1,000 - $200,000

## Prompt Engineering

The LLM service uses carefully crafted prompts for:

1. **Eligibility Explanations**: Clear, empathetic communication of decisions
2. **Conversation Management**: Natural flow progression and entity extraction
3. **Rejection Handling**: Constructive feedback with improvement suggestions

See `backend/app/prompts/templates.py` for prompt templates.

## Monitoring & Observability

### Splunk Dashboards

Pre-built queries for:
- Eligibility decisions distribution
- Response time percentiles
- Error rates
- Human handoff analysis
- Approval rates by loan type

### Alerts

Configured alerts for:
- High error rates
- Elevated response times
- Service availability
- Unusual rejection patterns

## Compliance Considerations

- Automatic disclaimer injection
- PII handling and masking
- Audit logging for all decisions
- Rate limiting to prevent abuse
- CORS configuration for security

## Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

## Deployment to GCP

1. **Build and push container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/loan-eligibility-agent
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy loan-eligibility-agent \
     --image gcr.io/PROJECT_ID/loan-eligibility-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Configure Dialogflow CX webhook**
   - Set webhook URL to Cloud Run service URL
   - Enable authentication if required

## Skills Demonstrated

This project demonstrates proficiency in:

- ✅ Python backend development (FastAPI)
- ✅ RESTful API design
- ✅ Dialogflow CX conversation design
- ✅ Prompt engineering for LLMs
- ✅ Google Cloud Platform deployment
- ✅ Splunk monitoring and analytics
- ✅ Microservices architecture
- ✅ Financial services domain knowledge
- ✅ Compliance-aware development

## Future Enhancements

- [ ] Agent Development Kit (ADK) integration
- [ ] Apigee API management setup
- [ ] Multi-language support
- [ ] Voice channel integration
- [ ] A/B testing for prompts
- [ ] ML-based risk scoring

## License

This project is for portfolio/demonstration purposes.

## Contact

For questions about this project or collaboration opportunities, please reach out.
