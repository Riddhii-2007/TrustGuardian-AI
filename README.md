# 🛡️ TrustGuardian AI

**Enterprise Trust Intelligence Platform**

> *"Protecting Business Decisions Before Trust Is Exploited."*

Instead of asking *"Is this email malicious?"* — TrustGuardian asks **"Should this business trust this request?"**

---

## 🎯 What It Does

Prevents **Business Email Compromise (BEC)**, **CEO Fraud**, **Brand Impersonation**, and **Workflow Manipulation** by validating business requests using enterprise context, trust relationships, and AI.

## 🏗️ Architecture

```
React + TypeScript + Tailwind CSS
        │
        ▼
  Supabase Auth (Google OAuth)
        │
        ▼
    FastAPI Backend
        │
 ┌──────┼───────────────┐
 │      │               │
 ▼      ▼               ▼
Supabase    Neo4j      Groq
(Postgres)  Graph DB   (Llama 3)
```

## ⭐ Key Innovations

| Feature | Description |
|---------|-------------|
| **Decision Sandbox™** | Simulates "What happens if this request is approved?" before execution |
| **Trust Replay™** | Compares expected workflow vs actual workflow to detect deviations |
| **Human Psychology Engine** | Models urgency, authority, fear, familiarity, and intent signals |
| **Enterprise Knowledge Graph** | Maps organizational trust relationships in Neo4j |
| **Explainable AI** | Returns risk score + reasoning chain + actionable recommendation |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (for Neo4j)
- Supabase account
- Groq API key

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # Configure your environment
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env    # Configure your environment
uvicorn app.main:app --reload
```

### Database (Docker)

```bash
docker compose up -d    # Starts Neo4j + PostgreSQL
```

## 📁 Project Structure

```
TrustGuardian AI/
├── frontend/          # React + TypeScript + Tailwind CSS
├── backend/           # FastAPI + Python
├── database/          # SQL & Cypher schemas
├── docs/              # Documentation
├── docker-compose.yml # Local dev infrastructure
└── README.md
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind CSS, Cytoscape.js |
| Backend | FastAPI, Python |
| Auth | Supabase Auth (Google OAuth) |
| Database | Supabase PostgreSQL |
| Graph DB | Neo4j |
| AI/LLM | Llama 3 via Groq API |
| Email | Gmail API (client-side) |

## 📄 License

MIT
