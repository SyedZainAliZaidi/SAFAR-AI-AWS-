# Safar AI - Backend API
## CockroachDB x AWS Hackathon — Build with Agentic Memory

**Developer:** Sara ZEROUAL — Backend Logic Development  
**Institution:** ENSAM Casablanca, MSEI (Energy & Industrial Systems)  
**Hackathon:** CockroachDB × AWS — Build with Agentic Memory  
**Submission Deadline:** August 18, 2026

---

## Project Overview

Safar AI is a multi-service AI-powered travel platform designed for the Moroccan and African market. The application provides instant access to 36 distinct digital services — flights, trains, hotels, taxis, ride-hailing, travel insurance, and AI-powered assistance — all within a single interface.

The backend architecture was built around **CockroachDB** as the primary persistent database, leveraging its distributed SQL capabilities and PostgreSQL compatibility. The system implements **Agentic Memory**: the AI retains user preferences, booking history, and conversational context across sessions, enabling truly personalized travel assistance.

### What is Agentic Memory?

Traditional chatbots forget everything when the session ends. With Agentic Memory powered by CockroachDB:

- A user states: *"I am vegetarian, my budget is 500€, and I prefer window seats on direct flights."*
- The application closes.
- Three days later, the user returns and simply asks: *"Find me a flight to Paris."*
- The AI responds: *"I found a direct flight for 450€ with vegetarian meal option and a window seat. Shall I proceed with booking?"*

All preferences are stored persistently in CockroachDB and retrieved automatically by the AI via AWS Bedrock integration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (36 Screens)                    │
│              React / Next.js — 4 Sets × 9 Modules            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / REST JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS API Gateway                            │
│         Routes requests to correct Lambda functions          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS Lambda (Python/Flask)                  │
│                    Backend API Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ User Mgmt    │  │ Agentic      │  │ Booking      │       │
│  │ /api/v1/     │  │ Memory       │  │ /api/v1/     │       │
│  │ users        │  │ /api/v1/chat │  │ bookings     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ CockroachDB  │ │ AWS Bedrock  │ │ Amazon S3    │
    │ Persistent   │ │ AI/LLM       │ │ Static       │
    │ Memory + Data│ │ Responses    │ │ Assets       │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Why CockroachDB?

CockroachDB was selected as the primary database for four strategic reasons aligned with the hackathon theme:

1. **Distributed SQL Architecture** — Horizontally scalable across regions, essential for a travel platform serving Morocco, Africa, and eventually global markets.
2. **ACID Transactions** — Critical for booking and payment operations where data consistency is non-negotiable.
3. **PostgreSQL Compatibility** — Seamless integration with Python `psycopg2`, AWS Lambda, and existing SQL expertise.
4. **Cloud-Native Design** — Native integration with AWS infrastructure and serverless computing models.

*Note: DynamoDB and RDS are retained in the architecture for high-speed caching and specific AWS-native workflows, but CockroachDB serves as the authoritative persistent layer.*

---

## Database Schema (CockroachDB)

### Core Tables

| Table | Purpose | Hackathon Relevance |
|-------|---------|---------------------|
| `users` | User profiles, authentication, localization | Multi-region user base |
| `user_preferences` | **Agentic Memory core** — AI remembers preferences | **Primary judging criterion** |
| `conversations` | Persistent chat history with intent extraction | Contextual AI responses |
| `bookings` | Flight, train, hotel, taxi reservations | Real-world utility |
| `services` | Catalog of all 36 service modules | Frontend integration |
| `ai_memory_context` | Processed memory summaries for AWS Bedrock | Semantic AI context |

### Key Design Decisions

- **UUID Primary Keys** — Globally unique identifiers prevent collision in distributed deployments.
- **JSONB Columns** — Flexible schema for booking details and extracted entities without rigid migrations.
- **Composite Indexes** — Optimized queries for `user_id + preference_type` and `user_id + created_at`.
- **Upsert Logic** — Preferences are updated in-place rather than duplicated, maintaining a single source of truth.

---

## API Endpoints

### Health & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Database connectivity and version check |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/register` | Register new user with profile |
| GET | `/api/v1/users/{user_id}/profile` | Retrieve profile + all agentic memory |

### Agentic Memory (Hackathon Core)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/{user_id}/preferences` | Save/update a preference in AI memory |
| GET | `/api/v1/users/{user_id}/preferences` | Retrieve all active preferences |

### AI Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Conversational AI with memory context retrieval |

### Booking Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/bookings` | Create new booking |
| GET | `/api/v1/bookings/{user_id}` | Retrieve user booking history |

### Services Catalog
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/services` | List all 36 services (filterable by set/category) |

---

## Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Language | Python 3.11 | Backend logic |
| Framework | Flask | REST API server |
| Database | CockroachDB Cloud | Persistent storage + Agentic Memory |
| ORM/Connector | psycopg2 | PostgreSQL-compatible database driver |
| AI/LLM | AWS Bedrock (Claude) | Conversational intelligence |
| Serverless | AWS Lambda | Scalable compute |
| Gateway | AWS API Gateway | Request routing |
| Storage | Amazon S3 | Static assets & documents |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- CockroachDB Cloud account (free tier)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sara-zeroual/safar-ai-backend.git
cd safar-ai-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL to your CockroachDB connection string

# 5. Initialize database
psql $DATABASE_URL -f 01_schema_cockroachdb.sql

# 6. Run the application
python 02_backend_api.py
```

### Verify Installation

```bash
curl http://localhost:5000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "CockroachDB",
  "version": "v24.1.x",
  "timestamp": "2026-08-12T12:00:00"
}
```

---

## AWS Lambda Deployment

The backend includes a `lambda_handler` function for serverless deployment:

```python
def lambda_handler(event, context):
    from aws_wsgi import response
    return response(app, event, context)
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | CockroachDB connection string | `postgresql://user:pass@host:26257/db?sslmode=require` |
| `AWS_REGION` | AWS deployment region | `eu-central-1` |
| `BEDROCK_MODEL_ID` | AWS Bedrock model identifier | `anthropic.claude-3-sonnet-20240229-v1:0` |

### Deployment Steps

1. Package dependencies with `pip install -r requirements.txt -t package/`
2. Zip application code + dependencies
3. Upload to AWS Lambda (Python 3.11 runtime)
4. Configure API Gateway routes matching the endpoints above
5. Set environment variables in Lambda configuration

---

## Hackathon Judging Criteria Mapping

| Criterion | Implementation | File |
|-----------|---------------|------|
| **Agentic Memory (20%)** | `user_preferences` table + `ai_memory_context` + memory retrieval in `/api/v1/chat` | `01_schema_cockroachdb.sql`, `02_backend_api.py` |
| **Technical Implementation (20%)** | CockroachDB as primary database, ACID transactions, composite indexes, upsert logic | `01_schema_cockroachdb.sql` |
| **Real-World Impact (20%)** | 36-service travel platform for Morocco/Africa, booking system, multi-currency | All files |
| **Production Readiness (20%)** | Health checks, input validation, error handling, AWS Lambda handler, CORS | `02_backend_api.py` |
| **Creativity (20%)** | Agentic Memory concept applied to travel (not just generic chat), semantic context for Bedrock | Architecture + README |

---

## Team Integration

| Member | Responsibility | Integration Point |
|--------|---------------|-------------------|
| Sara ZEROUAL | Backend Logic + CockroachDB Schema + API Development | Database design, API endpoints, documentation |
| Syed Zain | AWS Cloud Infrastructure | Lambda deployment, API Gateway, Bedrock integration |
| Muntaha | Frontend Integration | Connects React UI to `/api/v1/services` and `/api/v1/users` |
| Maruf | Frontend Integration | Connects forms to `/api/v1/bookings` and `/api/v1/chat` |
| Nasir | Presentation & UI Polish | Pitch deck, demo video, README review |

---

## Files in This Repository

| File | Description |
|------|-------------|
| `01_schema_cockroachdb.sql` | Complete CockroachDB schema with tables, indexes, and initial data (36 services + demo user) |
| `02_backend_api.py` | Flask REST API with all endpoints, Agentic Memory logic, and AWS Lambda handler |
| `requirements.txt` | Python dependencies (Flask, psycopg2, CORS, aws-wsgi) |
| `README.md` | This file — architecture, setup, and deployment documentation |

---

## License

Apache 2.0 — See LICENSE file
