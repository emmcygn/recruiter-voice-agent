# Voice AI Candidate Screening Agent

A production-shaped demonstration of a **voice AI agent** that conducts structured candidate screening interviews for software engineering roles.

Built with **Retell AI** (voice layer) and **FastAPI** (orchestration backend). The agent asks 5 structured questions, scores responses via deterministic keyword extraction, and persists structured JSON scorecards.

## Why This Approach

Voice AI in recruitment fails when it's treated as a chatbot with speech. This system proves that **deterministic, backend-validated voice agents** can deliver structured, auditable screening at scale.

- **Backend as Source of Truth**: The agent never confirms outcomes without explicit backend validation
- **Deterministic Scoring**: Keyword-based extraction, no LLM scoring — observable and reproducible
- **Observability First**: Every screening is persisted with per-question scores, rationales, and full transcript
- **GDPR-Aware**: Consent collection built into the call flow

## Quick Start

```bash
# Install dependencies
pip install -r voice_agents_demo/requirements.txt

# Run in Demo Mode (deterministic scores, always passes)
cd voice_agents_demo && DEMO_MODE=true python main.py

# Run in Normal Mode (keyword-based scoring)
cd voice_agents_demo && python main.py

# Run tests
cd voice_agents_demo && python -m pytest test_screening.py -v
```

The server starts at `http://localhost:8000`.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST /submit-screening` | Submit candidate screening for scoring | Core endpoint |
| `GET /screenings` | List all screening scorecards | |
| `GET /screenings/{id}` | Get a single scorecard by ID | |
| `POST /retell/function` | Retell mid-call custom function handler | Called by voice agent |
| `POST /webhook/retell` | Retell post-call webhook | Logs transcripts |
| `GET /health` | Health check | |

## Screening Flow

1. Voice agent greets candidate, collects GDPR consent
2. Asks 5 structured questions: Experience, Tech Stack, Problem-Solving, Collaboration, Availability
3. Calls `submit_screening` custom function with answers
4. Backend scores each answer via keyword extraction (1-5 scale)
5. Returns overall pass/flag/fail status with per-question rationales
6. Agent reads confirmation to candidate
7. Post-call webhook logs full transcript

## Scoring Model

Each answer is scored 1-5 based on keyword matching:

- **Experience**: Years parsed + title keywords (senior/lead/staff)
- **Tech Stack**: Count of recognized technologies against target list
- **Problem-Solving**: Methodology signal words (debugged, profiled, tested, etc.)
- **Collaboration**: Collaboration keywords (pair, review, PR, retro, etc.)
- **Availability**: Notice period parsing (immediate → 3+ months)

**Overall status**: pass (avg >= 3.5), flag (avg >= 2.5), fail (avg < 2.5)

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `DEMO_MODE` | Deterministic scores, always passes | `false` |

## Extension Points (Not Built)

The `/retell/function` endpoint routes by function name. Adding new agent modes requires: a new Retell prompt, a new function handler, and new Pydantic models.

### GDPR Consent Agent
Outbound call to collect explicit data retention opt-in. Function: `submit_consent`, Endpoint: `POST /submit-consent`.

### No-Show Confirmation Agent
Day-before call to confirm interview attendance and flag no-show risk. Function: `submit_confirmation`, Endpoint: `POST /submit-confirmation`.

## Tech Stack

- **Voice**: Retell AI (single-prompt agent, custom functions, webhooks)
- **Backend**: Python, FastAPI, Pydantic v2
- **Persistence**: Flat JSON file (`screenings.json`)
- **Testing**: pytest

## Related

- [talent-tool-mvp](https://github.com/emmcygn/talent-tool-mvp) — AI-powered recruitment platform with candidate matching, scoring, and pipeline management
