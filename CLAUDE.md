# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice AI candidate screening agent: a **Single-Prompt Retell AI voice agent** backed by a **FastAPI orchestration server** that conducts structured software engineer screening interviews, scores candidates via keyword extraction, and persists JSON scorecards.

## Commands

```bash
# Install dependencies
pip install -r voice_agents_demo/requirements.txt

# Run server (demo mode - deterministic scores, always passes)
cd voice_agents_demo && DEMO_MODE=true python main.py

# Run server (normal mode - keyword-based scoring)
cd voice_agents_demo && python main.py

# Run all tests
cd voice_agents_demo && python -m pytest test_screening.py -v

# Run a single test class
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreExperience -v

# Run a single test
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreExperience::test_senior_five_plus_years -v
```

## Architecture

Three-layer system:

1. **Voice Layer** (Retell AI, external) — Single-prompt agent configured via dashboard, triggers `submit_screening` custom function mid-call.

2. **Orchestration Layer** (`voice_agents_demo/`):
   - `main.py` — FastAPI app: Pydantic models (`ScreeningSubmission`, `ScreeningScorecard`), endpoints (`/submit-screening`, `/screenings`, `/retell/function`), persistence, DEMO_MODE logic.
   - `scorer.py` — Keyword-based scoring functions: `score_experience`, `score_tech_stack`, `score_problem_solving`, `score_collaboration`, `score_availability`, `compute_overall`.
   - `webhook_handler.py` — Retell post-call webhooks (`/webhook/retell`). Imports `app` from `main.py`.
   - `test_screening.py` — pytest test suite for all scoring and endpoint logic.
   - `retell_agent_prompt.md` — Voice agent prompt (pasted into Retell dashboard, not consumed by backend).

3. **Persistence** — `screenings.json` (gitignored) stores all screening records as flat JSON.

### Key Data Flow

Retell agent collects answers → calls `submit_screening` → POST to `/retell/function` → scores via keyword extraction in `scorer.py` → persists scorecard → returns result → agent speaks confirmation → `call_ended` webhook logs transcript.

### Environment Variables

- `DEMO_MODE` — `true` for deterministic, always-pass scorecards (demo use)
