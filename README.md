# SwitchedOn London — Demo-Grade Voice Agent System

A production-shaped demonstration of a **Single-Prompt Voice AI Agent** designed for SwitchedOn London, leveraging **Retell AI** and a **FastAPI** orchestration backend.

This repository demonstrates the technical and strategic framework required to deploy reliable, deterministic voice agents in a high-stakes service business environment.

---

## Project Intent

The objective of this demo is to prove that voice AI can be both **deterministic** and **highly observable**. Built as a "Founding Solutions Engineer" demonstration, it emphasizes clean system boundaries, backend-validated actions, and a consultative approach to deployment.

### Core Principles
- **Backend as Source of Truth**: The agent never confirms a booking without explicit confirmation from the logic layer. No hallucinations.
- **Reliability over Breadth**: High confidence in core booking flows over a wide range of half-baked features.
- **Observability First**: Every interaction, decision, and transcript is persisted and inspectable.
- **Demo-Grade Polish**: Optimized for reproducible, predictable live demonstrations via a dedicated `DEMO_MODE`.

---

## System Architecture

The system is partitioned into three distinct layers to ensure scalability and maintainability.

### 1. Voice Layer (Retell AI)
- **Single-Prompt Strategy**: Predictable conversational flow without the complexity of state-machine-heavy alternatives.
- **Deterministic Slot Filling**: Robust extraction of PII (Name, Phone) and service details.
- **Real-Time Tooling**: Mid-call custom functions allow the agent to "act" (check availability/book) while the customer is on the line.

### 2. Orchestration Layer (FastAPI)
- **Booking Hub**: Validates required slots and executes business logic.
- **Webhook Integration**: Captures post-call lifecycle events and final transcripts.
- **Simulation Engine**: Supports deterministic booking references and success rates for demo environments.

### 3. Persistence Layer
- **Structured Logging**: Every call is stored in `calls.json` with full metadata, transcripts, and backend decision traces.

---

## Key Features

- **Live Appointment Booking**: End-to-end flow from phone greeting to spoke booking reference.
- **Business Knowledge-Aware**: The agent is trained on SwitchedOn's real pricing (£99-109/hr), South West London coverage, and core services (Plumbing, Electrical, Heating).
- **Robust Communication**: Native support for NATO phonetics for postcodes, proactive name spelling, and 2026 date normalization.
- **Safety & Escalation**: Automatic detection of misunderstanding or human-agent requests with graceful handover logging.

---

## Documentation Index

Strategic documentation designed for client-facing deployment:

- **[ONBOARDING.md](voice_agents_demo/ONBOARDING.md)**: A 6-phase framework for taking a client from Discovery to Full Rollout.
- **[QUALITY_MONITORING.md](voice_agents_demo/QUALITY_MONITORING.md)**: A comprehensive strategy for monitoring KPIs, sentiment, and transcript accuracy.
- **[SPECIFICATION.md](voice_agents_demo/SPECIFICATION.md)**: The authoritative technical specification and design constraints.
- **[STATUS.md](voice_agents_demo/STATUS.md)**: Current build state, test results, and implementation roadmap.

---

## Quick Start

### Prerequisites
- Python 3.8+
- Retell AI API Key (for live integration)

### Installation
```bash
# Clone the repository
git clone <repo-url>
cd voice_demo

# Install dependencies
pip install -r voice_agents_demo/requirements.txt
```

### Running the Backend
```bash
cd voice_agents_demo

# Run in Demo Mode (deterministic references, 100% success rate)
DEMO_MODE=true python main.py

# Run in Normal Mode (simulated reality)
python main.py
```
The server will start at `http://localhost:8000`.

---

## API Interface

- **`POST /attempt-booking`**: Primary orchestration endpoint (called by Retell).
- **`GET /calls`**: Retrieve all historical call records and transcripts.
- **`GET /health`**: System health check.
- **`POST /webhook/retell`**: Post-call event processing.

---

## Strategic Deferrals (Future Roadmap)

To maintain demo confidence, the following are explicitly scoped for post-MVP rollout:
- **Cal.com Integration**: Real-time calendar writes via API.
- **SMS/Email Notifications**: Post-booking confirmation delivery.
- **Performance Dashboard**: Visualization of Retell analytics and backend KPIs.

---

## License

Demo project for professional assessment purposes. Built by **Emmanuel Cuyugan**.
