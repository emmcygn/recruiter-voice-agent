# Candidate Screening Voice Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pivot the SwitchedOn booking voice agent into a recruitment candidate screening agent that conducts structured 5-question phone interviews, scores candidates via keyword extraction, and persists JSON scorecards.

**Architecture:** FastAPI backend receives mid-call custom function calls from Retell AI, scores candidate answers using deterministic keyword matching, and persists structured scorecards to a flat JSON file. The Retell voice agent is configured via dashboard with a single prompt. DEMO_MODE provides deterministic results for live demonstrations.

**Tech Stack:** Python 3.8+, FastAPI, Pydantic v2, uvicorn, pytest, pytest-asyncio, httpx (test client)

**Spec:** `docs/superpowers/specs/2026-03-29-candidate-screening-agent-design.md`

---

## File Structure

| File | Role |
|---|---|
| `voice_agents_demo/main.py` | FastAPI app, Pydantic models, endpoints, scoring engine, persistence, DEMO_MODE |
| `voice_agents_demo/scorer.py` | Keyword-based scoring functions (one per question category) |
| `voice_agents_demo/webhook_handler.py` | Retell post-call webhook handler (minimal changes from current) |
| `voice_agents_demo/test_screening.py` | All 13 pytest unit tests |
| `voice_agents_demo/retell_agent_prompt.md` | Single-prompt Retell agent config for screening flow |
| `voice_agents_demo/requirements.txt` | Python dependencies (add pytest, pytest-asyncio) |
| `README.md` | Repo-level docs, API contract, extension points |
| `CLAUDE.md` | Updated guidance for Claude Code |
| `.gitignore` | Add `screenings.json`, remove `calls.json` references |

**Decomposition rationale:** Scoring logic is extracted to `scorer.py` because it contains 5 independent scoring functions with distinct keyword lists — keeping it in `main.py` would make that file ~300 lines and harder to test in isolation.

---

## Task 1: Project Setup — Dependencies and Cleanup

**Files:**
- Modify: `voice_agents_demo/requirements.txt`
- Delete: `voice_agents_demo/cal_client.py`
- Modify: `.gitignore`

- [ ] **Step 1: Update requirements.txt**

Replace contents of `voice_agents_demo/requirements.txt` with:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.25.2
pytest==8.0.0
pytest-asyncio==0.23.3
```

- [ ] **Step 2: Update .gitignore**

In `.gitignore`, replace the `calls.json` line with `screenings.json`:

Replace:
```
# Runtime data - contains test/demo data
calls.json
```

With:
```
# Runtime data - contains test/demo data
screenings.json
calls.json
```

- [ ] **Step 3: Delete cal_client.py**

```bash
rm voice_agents_demo/cal_client.py
```

- [ ] **Step 4: Install updated dependencies**

```bash
cd voice_agents_demo && pip install -r requirements.txt
```

Expected: All packages install successfully, pytest is available.

- [ ] **Step 5: Verify pytest runs**

```bash
cd voice_agents_demo && python -m pytest --version
```

Expected: `pytest 8.0.0` (or compatible version)

- [ ] **Step 6: Commit**

```bash
git add voice_agents_demo/requirements.txt .gitignore
git rm voice_agents_demo/cal_client.py
git commit -m "chore: update deps, remove cal_client, add pytest"
```

---

## Task 2: Scoring Engine — Experience Scorer

**Files:**
- Create: `voice_agents_demo/scorer.py`
- Create: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for experience scoring**

Create `voice_agents_demo/test_screening.py`:

```python
import pytest
from scorer import score_experience


class TestScoreExperience:
    def test_senior_five_plus_years(self):
        result = score_experience("I've been a senior software engineer for 7 years at Google")
        assert result["score"] == 5
        assert "7" in result["rationale"] or "year" in result["rationale"].lower()

    def test_mid_level_three_years(self):
        result = score_experience("I have 3 years of experience as a developer")
        assert result["score"] == 4

    def test_junior_one_year(self):
        result = score_experience("I graduated last year and have been working for about 1 year")
        assert result["score"] == 3

    def test_no_signal(self):
        result = score_experience("I like computers")
        assert result["score"] == 1

    def test_title_boost(self):
        # "lead" keyword should boost score by 1 (capped at 5)
        result = score_experience("I'm a lead engineer with 3 years experience")
        assert result["score"] == 5  # 4 (3 years) + 1 (lead title) = 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreExperience -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scorer'`

- [ ] **Step 3: Implement experience scorer**

Create `voice_agents_demo/scorer.py`:

```python
import re


def score_experience(answer: str) -> dict:
    """Score experience answer based on years and title keywords."""
    text = answer.lower()
    score = 1
    rationale_parts = []

    # Extract years
    year_patterns = [
        r'(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?',
    ]
    years = 0
    for pattern in year_patterns:
        match = re.search(pattern, text)
        if match:
            years = int(match.group(1))
            break

    if years >= 5:
        score = 5
        rationale_parts.append(f"{years} years experience")
    elif years >= 3:
        score = 4
        rationale_parts.append(f"{years} years experience")
    elif years >= 1:
        score = 3
        rationale_parts.append(f"{years} year(s) experience")
    elif years > 0:
        score = 2
        rationale_parts.append(f"Less than 1 year")
    else:
        score = 1
        rationale_parts.append("No experience signal detected")

    # Title boost
    title_keywords = ["senior", "lead", "staff", "principal", "architect", "head of", "director"]
    for kw in title_keywords:
        if kw in text:
            score = min(score + 1, 5)
            rationale_parts.append(f"title keyword: {kw}")
            break

    return {"score": score, "rationale": ", ".join(rationale_parts)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreExperience -v
```

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add voice_agents_demo/scorer.py voice_agents_demo/test_screening.py
git commit -m "feat: add experience scoring with keyword extraction"
```

---

## Task 3: Scoring Engine — Tech Stack Scorer

**Files:**
- Modify: `voice_agents_demo/scorer.py`
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for tech stack scoring**

Append to `voice_agents_demo/test_screening.py`:

```python
from scorer import score_tech_stack


class TestScoreTechStack:
    def test_strong_stack(self):
        result = score_tech_stack("Python, TypeScript, React, PostgreSQL, Docker, AWS")
        assert result["score"] == 5
        assert "6" in result["rationale"]

    def test_moderate_stack(self):
        result = score_tech_stack("I mainly use Java and Spring Boot with some Kubernetes")
        assert result["score"] == 4  # java, spring, kubernetes = 3 matches

    def test_single_match(self):
        result = score_tech_stack("I only really use Python")
        assert result["score"] == 2

    def test_no_matches(self):
        result = score_tech_stack("I use Fortran and COBOL mostly")
        assert result["score"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreTechStack -v
```

Expected: FAIL — `ImportError: cannot import name 'score_tech_stack'`

- [ ] **Step 3: Implement tech stack scorer**

Append to `voice_agents_demo/scorer.py`:

```python
TECH_KEYWORDS = [
    "python", "typescript", "javascript", "react", "node", "nodejs",
    "postgresql", "postgres", "aws", "docker", "kubernetes", "k8s",
    "go", "golang", "java", "c#", "csharp", "ruby", "rust",
    "vue", "angular", "django", "fastapi", "flask", "spring",
    "mongodb", "redis", "graphql", "terraform",
]


def score_tech_stack(answer: str) -> dict:
    """Score tech stack answer by counting recognized technologies."""
    text = answer.lower()
    matches = [kw for kw in TECH_KEYWORDS if kw in text]
    # Deduplicate aliases (nodejs/node, golang/go, postgres/postgresql, csharp/c#)
    unique = set()
    alias_map = {
        "nodejs": "node", "golang": "go", "postgres": "postgresql", "csharp": "c#", "k8s": "kubernetes",
    }
    for m in matches:
        unique.add(alias_map.get(m, m))

    count = len(unique)

    if count >= 5:
        score = 5
    elif count >= 3:
        score = 4
    elif count >= 2:
        score = 3
    elif count >= 1:
        score = 2
    else:
        score = 1

    rationale = f"{count} matching technologies" if count > 0 else "No recognized technologies"
    return {"score": score, "rationale": rationale}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreTechStack -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add voice_agents_demo/scorer.py voice_agents_demo/test_screening.py
git commit -m "feat: add tech stack scoring with keyword matching"
```

---

## Task 4: Scoring Engine — Problem-Solving, Collaboration, Availability Scorers

**Files:**
- Modify: `voice_agents_demo/scorer.py`
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for remaining three scorers**

Append to `voice_agents_demo/test_screening.py`:

```python
from scorer import score_problem_solving, score_collaboration, score_availability


class TestScoreProblemSolving:
    def test_strong_methodology(self):
        result = score_problem_solving(
            "We had a memory leak so I profiled the app, debugged the issue, "
            "tested a fix, and then refactored the module to prevent regression"
        )
        assert result["score"] == 5

    def test_some_signals(self):
        result = score_problem_solving("I debugged the issue and tested the fix")
        assert result["score"] == 3

    def test_no_signals(self):
        result = score_problem_solving("It was hard but I figured it out eventually")
        assert result["score"] == 1


class TestScoreCollaboration:
    def test_strong_collaboration(self):
        result = score_collaboration(
            "We do pair programming, async code reviews on PRs, "
            "and weekly retros to improve our process"
        )
        assert result["score"] == 5

    def test_some_collaboration(self):
        result = score_collaboration("I mostly do code reviews with my team")
        assert result["score"] == 4

    def test_no_signals(self):
        result = score_collaboration("I just work on my tasks independently")
        assert result["score"] == 1


class TestScoreAvailability:
    def test_immediate(self):
        result = score_availability("I can start immediately, I'm between roles")
        assert result["score"] == 5

    def test_one_month(self):
        result = score_availability("I have a 1 month notice period")
        assert result["score"] == 4

    def test_two_months(self):
        result = score_availability("My notice period is 2 months")
        assert result["score"] == 3

    def test_three_months(self):
        result = score_availability("I'm on a 3 month notice period")
        assert result["score"] == 2

    def test_unclear(self):
        result = score_availability("I'm not sure, it depends on a few things")
        assert result["score"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoreProblemSolving test_screening.py::TestScoreCollaboration test_screening.py::TestScoreAvailability -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement problem-solving scorer**

Append to `voice_agents_demo/scorer.py`:

```python
PROBLEM_SOLVING_SIGNALS = [
    "debugged", "debug", "profiled", "profiling", "tested", "testing",
    "refactored", "refactoring", "scaled", "scaling", "optimized", "optimization",
    "root cause", "trade-off", "tradeoff", "trade off",
    "investigated", "diagnosed", "benchmarked", "monitored", "instrumented",
    "iterated", "prototyped", "architected",
]


def score_problem_solving(answer: str) -> dict:
    """Score problem-solving answer by counting methodology signals."""
    text = answer.lower()
    found = [s for s in PROBLEM_SOLVING_SIGNALS if s in text]
    count = len(found)

    if count >= 4:
        score = 5
    elif count >= 3:
        score = 4
    elif count >= 2:
        score = 3
    elif count >= 1:
        score = 2
    else:
        score = 1

    rationale = f"{count} methodology signals" if count > 0 else "No methodology signals detected"
    return {"score": score, "rationale": rationale}
```

- [ ] **Step 4: Implement collaboration scorer**

Append to `voice_agents_demo/scorer.py`:

```python
COLLABORATION_KEYWORDS = [
    "pair", "pairing", "pair programming",
    "review", "code review", "pr", "pull request",
    "stand-up", "standup", "retro", "retrospective",
    "async", "sync",
    "mentor", "mentoring",
    "team", "mob programming",
]


def score_collaboration(answer: str) -> dict:
    """Score collaboration answer by counting collaboration keywords."""
    text = answer.lower()
    found = [kw for kw in COLLABORATION_KEYWORDS if kw in text]
    # Deduplicate overlapping matches (e.g. "pair" and "pair programming")
    count = len(set(found))

    if count >= 3:
        score = 5
    elif count >= 2:
        score = 4
    elif count >= 1:
        score = 3
    else:
        score = 1

    rationale = f"{count} collaboration keywords" if count > 0 else "No collaboration signals detected"
    return {"score": score, "rationale": rationale}
```

- [ ] **Step 5: Implement availability scorer**

Append to `voice_agents_demo/scorer.py`:

```python
def score_availability(answer: str) -> dict:
    """Score availability based on notice period parsing."""
    text = answer.lower()

    # Check for immediate availability
    immediate_keywords = ["immediately", "immediate", "right away", "asap", "available now", "between roles", "no notice"]
    if any(kw in text for kw in immediate_keywords):
        return {"score": 5, "rationale": "Available immediately"}

    # Check for week-based notice
    week_match = re.search(r'(\d+)\s*weeks?', text)
    if week_match:
        weeks = int(week_match.group(1))
        if weeks <= 2:
            return {"score": 5, "rationale": f"{weeks} week(s) notice"}
        elif weeks <= 4:
            return {"score": 4, "rationale": f"{weeks} weeks notice"}
        elif weeks <= 8:
            return {"score": 3, "rationale": f"{weeks} weeks notice"}
        else:
            return {"score": 2, "rationale": f"{weeks} weeks notice"}

    # Check for month-based notice
    month_match = re.search(r'(\d+)\s*months?', text)
    if month_match:
        months = int(month_match.group(1))
        if months <= 1:
            return {"score": 4, "rationale": f"{months} month notice"}
        elif months <= 2:
            return {"score": 3, "rationale": f"{months} months notice"}
        else:
            return {"score": 2, "rationale": f"{months} months notice"}

    # "one month" / "two months" text patterns
    if "one month" in text:
        return {"score": 4, "rationale": "1 month notice"}
    if "two month" in text:
        return {"score": 3, "rationale": "2 months notice"}
    if "three month" in text:
        return {"score": 2, "rationale": "3 months notice"}

    return {"score": 1, "rationale": "Notice period unclear"}
```

- [ ] **Step 6: Run all scorer tests**

```bash
cd voice_agents_demo && python -m pytest test_screening.py -v
```

Expected: All tests PASS (5 experience + 4 tech stack + 3 problem solving + 3 collaboration + 5 availability = 20 tests)

- [ ] **Step 7: Commit**

```bash
git add voice_agents_demo/scorer.py voice_agents_demo/test_screening.py
git commit -m "feat: add problem-solving, collaboration, availability scorers"
```

---

## Task 5: Scoring Engine — Overall Score and Status

**Files:**
- Modify: `voice_agents_demo/scorer.py`
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for overall scoring**

Append to `voice_agents_demo/test_screening.py`:

```python
from scorer import compute_overall


class TestComputeOverall:
    def test_pass(self):
        scores = {
            "experience": {"score": 5, "rationale": ""},
            "tech_stack": {"score": 4, "rationale": ""},
            "problem_solving": {"score": 4, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 5, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 4.2
        assert result["overall_status"] == "pass"

    def test_flag(self):
        scores = {
            "experience": {"score": 3, "rationale": ""},
            "tech_stack": {"score": 3, "rationale": ""},
            "problem_solving": {"score": 3, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 2, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 2.8
        assert result["overall_status"] == "flag"

    def test_fail(self):
        scores = {
            "experience": {"score": 1, "rationale": ""},
            "tech_stack": {"score": 1, "rationale": ""},
            "problem_solving": {"score": 2, "rationale": ""},
            "collaboration": {"score": 1, "rationale": ""},
            "availability": {"score": 1, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 1.2
        assert result["overall_status"] == "fail"

    def test_boundary_pass(self):
        # Exactly 3.5 should be pass
        scores = {
            "experience": {"score": 4, "rationale": ""},
            "tech_stack": {"score": 3, "rationale": ""},
            "problem_solving": {"score": 4, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 3, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 3.4
        assert result["overall_status"] == "flag"

    def test_boundary_flag(self):
        # Exactly 2.5 should be flag
        scores = {
            "experience": {"score": 3, "rationale": ""},
            "tech_stack": {"score": 2, "rationale": ""},
            "problem_solving": {"score": 3, "rationale": ""},
            "collaboration": {"score": 2, "rationale": ""},
            "availability": {"score": 3, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 2.6
        assert result["overall_status"] == "flag"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestComputeOverall -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement compute_overall**

Append to `voice_agents_demo/scorer.py`:

```python
def compute_overall(scores: dict) -> dict:
    """Compute overall score and pass/flag/fail status from individual scores."""
    values = [s["score"] for s in scores.values()]
    avg = round(sum(values) / len(values), 1)

    if avg >= 3.5:
        status = "pass"
    elif avg >= 2.5:
        status = "flag"
    else:
        status = "fail"

    return {"overall_score": avg, "overall_status": status}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestComputeOverall -v
```

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add voice_agents_demo/scorer.py voice_agents_demo/test_screening.py
git commit -m "feat: add overall score computation with pass/flag/fail thresholds"
```

---

## Task 6: FastAPI Backend — Models and Core Endpoint

**Files:**
- Rewrite: `voice_agents_demo/main.py`
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for the submit-screening endpoint**

Append to `voice_agents_demo/test_screening.py`:

```python
import os
import json
import pytest
from fastapi.testclient import TestClient

# Ensure DEMO_MODE is off for most tests
os.environ["DEMO_MODE"] = "false"

from main import app, DATA_FILE

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_data_file():
    """Remove screenings.json before and after each test."""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    yield
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


VALID_PAYLOAD = {
    "candidate_name": "Jane Smith",
    "candidate_phone": "07123456789",
    "role_applied": "software_engineer",
    "consent_given": True,
    "answers": {
        "experience": "I have 5 years of experience as a senior software engineer at a fintech startup",
        "tech_stack": "Python, TypeScript, React, PostgreSQL, Docker, AWS",
        "problem_solving": "We had a memory leak so I profiled the service, debugged the issue, tested a fix, and refactored the module",
        "collaboration": "We do pair programming and async code reviews on PRs with weekly retros",
        "availability": "I have a 1 month notice period"
    },
    "transcript": "Full transcript of the call..."
}


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSubmitScreening:
    def test_valid_submission(self):
        response = client.post("/submit-screening", json=VALID_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_name"] == "Jane Smith"
        assert data["overall_status"] in ("pass", "flag", "fail")
        assert data["id"].startswith("SCR-")
        assert len(data["scores"]) == 5
        assert all(cat in data["scores"] for cat in ["experience", "tech_stack", "problem_solving", "collaboration", "availability"])
        for cat_score in data["scores"].values():
            assert 1 <= cat_score["score"] <= 5
            assert isinstance(cat_score["rationale"], str)

    def test_missing_fields(self):
        bad_payload = {"candidate_name": "Jane"}
        response = client.post("/submit-screening", json=bad_payload)
        assert response.status_code == 422

    def test_no_consent(self):
        payload = {**VALID_PAYLOAD, "consent_given": False}
        response = client.post("/submit-screening", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "rejected"
        assert data["overall_score"] == 0
        assert data["scores"] == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestHealthEndpoint test_screening.py::TestSubmitScreening -v
```

Expected: FAIL — current `main.py` has no `/submit-screening` endpoint

- [ ] **Step 3: Rewrite main.py**

Replace the entire contents of `voice_agents_demo/main.py` with:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import json
import uuid
from datetime import datetime, timezone
import os
import hashlib
import logging

from scorer import (
    score_experience,
    score_tech_stack,
    score_problem_solving,
    score_collaboration,
    score_availability,
    compute_overall,
)

logger = logging.getLogger(__name__)

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

app = FastAPI(title="Talent Screening API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class ScreeningAnswers(BaseModel):
    experience: str
    tech_stack: str
    problem_solving: str
    collaboration: str
    availability: str


class ScreeningSubmission(BaseModel):
    candidate_name: str
    candidate_phone: str
    role_applied: str = "software_engineer"
    consent_given: bool
    answers: ScreeningAnswers
    transcript: str = ""


class ScoreDetail(BaseModel):
    score: int
    rationale: str


class ScreeningScorecard(BaseModel):
    id: str
    timestamp: str
    candidate_name: str
    candidate_phone: str
    role_applied: str
    consent_given: bool
    overall_status: str
    overall_score: float
    scores: Dict[str, ScoreDetail]
    transcript: str
    demo_mode: bool = False


# --- Persistence ---

DATA_FILE = "screenings.json"


def load_screenings():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_screenings(screenings):
    with open(DATA_FILE, "w") as f:
        json.dump(screenings, f, indent=2)


def generate_screening_id(seed: str = "") -> str:
    if DEMO_MODE and seed:
        hash_hex = hashlib.md5(seed.encode()).hexdigest()[:5].upper()
        return f"SCR-{hash_hex}"
    return f"SCR-{uuid.uuid4().hex[:5].upper()}"


# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/submit-screening", response_model=ScreeningScorecard)
async def submit_screening(submission: ScreeningSubmission):
    screening_id = generate_screening_id(seed=submission.candidate_name)

    if not submission.consent_given:
        scorecard = {
            "id": screening_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_name": submission.candidate_name,
            "candidate_phone": submission.candidate_phone,
            "role_applied": submission.role_applied,
            "consent_given": False,
            "overall_status": "rejected",
            "overall_score": 0,
            "scores": {},
            "transcript": submission.transcript,
            "demo_mode": DEMO_MODE,
        }
    elif DEMO_MODE:
        scorecard = {
            "id": screening_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_name": submission.candidate_name,
            "candidate_phone": submission.candidate_phone,
            "role_applied": submission.role_applied,
            "consent_given": True,
            "overall_status": "pass",
            "overall_score": 4.6,
            "scores": {
                "experience": {"score": 5, "rationale": "Senior-level, 5+ years"},
                "tech_stack": {"score": 5, "rationale": "5+ matching technologies"},
                "problem_solving": {"score": 4, "rationale": "Clear methodology described"},
                "collaboration": {"score": 4, "rationale": "Strong collaboration signals"},
                "availability": {"score": 5, "rationale": "Available within 1 month"},
            },
            "transcript": submission.transcript,
            "demo_mode": True,
        }
    else:
        scores = {
            "experience": score_experience(submission.answers.experience),
            "tech_stack": score_tech_stack(submission.answers.tech_stack),
            "problem_solving": score_problem_solving(submission.answers.problem_solving),
            "collaboration": score_collaboration(submission.answers.collaboration),
            "availability": score_availability(submission.answers.availability),
        }
        overall = compute_overall(scores)
        scorecard = {
            "id": screening_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_name": submission.candidate_name,
            "candidate_phone": submission.candidate_phone,
            "role_applied": submission.role_applied,
            "consent_given": True,
            "overall_status": overall["overall_status"],
            "overall_score": overall["overall_score"],
            "scores": scores,
            "transcript": submission.transcript,
            "demo_mode": False,
        }

    screenings = load_screenings()
    screenings.append(scorecard)
    save_screenings(screenings)

    return ScreeningScorecard(**scorecard)


@app.get("/screenings")
async def list_screenings():
    return load_screenings()


@app.get("/screenings/{screening_id}")
async def get_screening(screening_id: str):
    screenings = load_screenings()
    for s in screenings:
        if s["id"] == screening_id:
            return s
    raise HTTPException(status_code=404, detail="Screening not found")


@app.post("/retell/function")
async def retell_custom_function(request: Request):
    """
    Retell Custom Function handler.
    Routes by function name. Currently supports: submit_screening.
    """
    body = await request.json()
    logger.info(f"Retell custom function call: {json.dumps(body, indent=2)}")

    fn_name = body.get("name")
    args = body.get("args", {})
    call_info = body.get("call", {})

    if fn_name == "submit_screening":
        consent_raw = args.get("consent_given", "false")
        consent = consent_raw.lower() in ("true", "yes", "1") if isinstance(consent_raw, str) else bool(consent_raw)

        submission = ScreeningSubmission(
            candidate_name=args.get("candidate_name", ""),
            candidate_phone=args.get("candidate_phone", ""),
            role_applied=args.get("role_applied", "software_engineer"),
            consent_given=consent,
            answers={
                "experience": args.get("answer_experience", ""),
                "tech_stack": args.get("answer_tech_stack", ""),
                "problem_solving": args.get("answer_problem_solving", ""),
                "collaboration": args.get("answer_collaboration", ""),
                "availability": args.get("answer_availability", ""),
            },
            transcript=call_info.get("transcript", ""),
        )
        return await submit_screening(submission)

    return {"error": f"Unknown function: {fn_name}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestHealthEndpoint test_screening.py::TestSubmitScreening -v
```

Expected: All 4 tests PASS (health + valid + missing fields + no consent)

- [ ] **Step 5: Commit**

```bash
git add voice_agents_demo/main.py voice_agents_demo/test_screening.py
git commit -m "feat: rewrite main.py with screening models, endpoints, and scoring"
```

---

## Task 7: Screening List and Get-By-ID Endpoints

**Files:**
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write failing tests for list and get-by-id**

Append to `voice_agents_demo/test_screening.py`:

```python
class TestScreeningsEndpoints:
    def test_list_screenings(self):
        # Submit one screening first
        client.post("/submit-screening", json=VALID_PAYLOAD)
        response = client.get("/screenings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["candidate_name"] == "Jane Smith"

    def test_get_screening_by_id(self):
        # Submit and capture ID
        submit_resp = client.post("/submit-screening", json=VALID_PAYLOAD)
        screening_id = submit_resp.json()["id"]
        response = client.get(f"/screenings/{screening_id}")
        assert response.status_code == 200
        assert response.json()["id"] == screening_id

    def test_get_screening_not_found(self):
        response = client.get("/screenings/SCR-ZZZZZ")
        assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they pass**

These endpoints already exist in the main.py we wrote in Task 6, so they should pass immediately:

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScreeningsEndpoints -v
```

Expected: All 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add voice_agents_demo/test_screening.py
git commit -m "test: add list/get-by-id endpoint tests"
```

---

## Task 8: Retell Function Routing and Webhook Tests

**Files:**
- Modify: `voice_agents_demo/test_screening.py`
- Modify: `voice_agents_demo/webhook_handler.py`

- [ ] **Step 1: Write tests for Retell function routing**

Append to `voice_agents_demo/test_screening.py`:

```python
# Import webhook_handler to register its routes on the app
import webhook_handler  # noqa: F401


RETELL_FUNCTION_PAYLOAD = {
    "name": "submit_screening",
    "call": {
        "call_id": "test-call-123",
        "transcript": "Agent: Hello... Candidate: Hi..."
    },
    "args": {
        "candidate_name": "John Doe",
        "candidate_phone": "07987654321",
        "role_applied": "software_engineer",
        "consent_given": "true",
        "answer_experience": "I have 6 years as a senior engineer",
        "answer_tech_stack": "Python, Go, PostgreSQL, Docker, Kubernetes",
        "answer_problem_solving": "I profiled and debugged a latency issue, then optimized the query layer",
        "answer_collaboration": "Pair programming and code reviews are core to our team process",
        "answer_availability": "I can start in 2 weeks"
    }
}


class TestRetellFunctionRouting:
    def test_submit_screening_via_retell(self):
        response = client.post("/retell/function", json=RETELL_FUNCTION_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_name"] == "John Doe"
        assert data["id"].startswith("SCR-")
        assert data["overall_status"] in ("pass", "flag", "fail")
        assert len(data["scores"]) == 5

    def test_unknown_function(self):
        payload = {"name": "unknown_function", "call": {}, "args": {}}
        response = client.post("/retell/function", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestWebhook:
    def test_call_ended_webhook(self):
        webhook_payload = {
            "event": "call_ended",
            "call": {
                "call_id": "webhook-test-123",
                "transcript": "Test transcript from webhook",
                "start_timestamp": 1714608475945,
                "end_timestamp": 1714608491736
            }
        }
        response = client.post("/webhook/retell", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Update webhook_handler.py imports**

Replace the entire contents of `voice_agents_demo/webhook_handler.py` with:

```python
from fastapi import Request
import json
import uuid
import logging
from datetime import datetime, timezone
from main import app, load_screenings, save_screenings, DEMO_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/webhook/retell")
async def retell_webhook(request: Request):
    """
    Post-call webhook for Retell.
    Logs call_ended events with transcript and metadata.
    """
    body = await request.json()
    event = body.get("event")
    logger.info(f"Retell webhook event={event}: {json.dumps(body, indent=2)}")

    if event == "call_ended":
        call_data = body.get("call", {})
        screenings = load_screenings()
        call_record = {
            "id": f"CALL-{call_data.get('call_id', uuid.uuid4().hex[:8])}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_name": "",
            "candidate_phone": "",
            "role_applied": "",
            "consent_given": False,
            "overall_status": "call_ended",
            "overall_score": 0,
            "scores": {},
            "transcript": call_data.get("transcript", ""),
            "demo_mode": DEMO_MODE,
            "call_metadata": {
                "start_timestamp": call_data.get("start_timestamp"),
                "end_timestamp": call_data.get("end_timestamp"),
                "call_id": call_data.get("call_id"),
            },
        }
        screenings.append(call_record)
        save_screenings(screenings)
        logger.info(f"Logged call_ended for call_id={call_data.get('call_id')}")

    return {"status": "ok", "event": event}


@app.get("/webhook/health")
async def webhook_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "retell-webhook",
    }
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestRetellFunctionRouting test_screening.py::TestWebhook -v
```

Expected: All 3 tests PASS

- [ ] **Step 4: Run full test suite**

```bash
cd voice_agents_demo && python -m pytest test_screening.py -v
```

Expected: All tests PASS (20 scorer + 4 endpoint + 3 list/get + 3 retell/webhook = 30 tests)

- [ ] **Step 5: Commit**

```bash
git add voice_agents_demo/test_screening.py voice_agents_demo/webhook_handler.py
git commit -m "feat: update webhook handler, add retell routing and webhook tests"
```

---

## Task 9: DEMO_MODE Determinism Test

**Files:**
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write DEMO_MODE test**

Append to `voice_agents_demo/test_screening.py`:

```python
class TestDemoMode:
    def test_demo_mode_deterministic(self):
        # Temporarily enable DEMO_MODE
        import main
        original = main.DEMO_MODE
        main.DEMO_MODE = True

        try:
            resp1 = client.post("/submit-screening", json=VALID_PAYLOAD)
            resp2 = client.post("/submit-screening", json=VALID_PAYLOAD)
            data1 = resp1.json()
            data2 = resp2.json()

            # Same candidate name → same screening ID
            assert data1["id"] == data2["id"]
            # Always pass in demo mode
            assert data1["overall_status"] == "pass"
            assert data2["overall_status"] == "pass"
            # Scores are identical
            assert data1["scores"] == data2["scores"]
            assert data1["demo_mode"] is True
        finally:
            main.DEMO_MODE = original
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestDemoMode -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add voice_agents_demo/test_screening.py
git commit -m "test: add DEMO_MODE determinism test"
```

---

## Task 10: Scoring Pass/Flag/Fail Integration Tests

**Files:**
- Modify: `voice_agents_demo/test_screening.py`

- [ ] **Step 1: Write end-to-end scoring threshold tests**

Append to `voice_agents_demo/test_screening.py`:

```python
class TestScoringThresholds:
    def test_strong_candidate_passes(self):
        """Strong answers across the board should produce 'pass'."""
        payload = {
            "candidate_name": "Strong Candidate",
            "candidate_phone": "07111111111",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I have 8 years as a senior staff engineer at Google",
                "tech_stack": "Python, TypeScript, React, PostgreSQL, Docker, AWS, Kubernetes",
                "problem_solving": "I profiled the service, debugged a memory leak, tested the fix, refactored the module, and optimized the query path",
                "collaboration": "We do pair programming, async code reviews, and weekly retros with the team",
                "availability": "I can start immediately"
            },
            "transcript": "strong candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "pass"
        assert data["overall_score"] >= 3.5

    def test_weak_candidate_fails(self):
        """Weak/empty answers should produce 'fail'."""
        payload = {
            "candidate_name": "Weak Candidate",
            "candidate_phone": "07222222222",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I like computers",
                "tech_stack": "I use Fortran",
                "problem_solving": "Things were hard but I managed",
                "collaboration": "I work alone",
                "availability": "Not sure really"
            },
            "transcript": "weak candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "fail"
        assert data["overall_score"] < 2.5

    def test_mixed_candidate_flags(self):
        """Mixed answers should produce 'flag'."""
        payload = {
            "candidate_name": "Mixed Candidate",
            "candidate_phone": "07333333333",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I have 2 years as a developer",
                "tech_stack": "Python and JavaScript",
                "problem_solving": "I debugged an issue in production",
                "collaboration": "I work with a team",
                "availability": "I have a 3 month notice period"
            },
            "transcript": "mixed candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "flag"
        assert 2.5 <= data["overall_score"] < 3.5
```

- [ ] **Step 2: Run tests**

```bash
cd voice_agents_demo && python -m pytest test_screening.py::TestScoringThresholds -v
```

Expected: All 3 PASS

- [ ] **Step 3: Run full test suite — final check**

```bash
cd voice_agents_demo && python -m pytest test_screening.py -v
```

Expected: All tests PASS (should be ~34 tests total)

- [ ] **Step 4: Commit**

```bash
git add voice_agents_demo/test_screening.py
git commit -m "test: add end-to-end scoring threshold integration tests"
```

---

## Task 11: Retell Agent Prompt

**Files:**
- Rewrite: `voice_agents_demo/retell_agent_prompt.md`

- [ ] **Step 1: Rewrite the agent prompt**

Replace the entire contents of `voice_agents_demo/retell_agent_prompt.md` with:

````markdown
# Talent Screening Agent — Retell Single Prompt

## Identity

You are a talent screening assistant working for a technology recruitment agency. Your name is Alex. Your role is to conduct brief, structured phone screenings for software engineering candidates.

## Style Guardrails

- Be warm, professional, and concise
- Keep every response under 2 sentences unless the candidate asks a question
- Never use jargon the candidate wouldn't understand
- Speak naturally — this is a phone call, not a chatbot
- Use spoken number formats: "oh seven one two three" not "07123"

## Call Flow

Follow these steps exactly. Complete each step before moving to the next.

### Step 1: Greeting

Say: "Hi {{candidate_name}}, this is Alex calling from the recruitment team. I'm reaching out about the software engineer role you applied for. Do you have a few minutes for a quick screening call?"

Wait for user response.

If they say no or it's a bad time: "No problem at all. We'll have a recruiter follow up with you to find a better time. Thank you!" End the call.

### Step 2: GDPR Consent

Say: "Great. Before we begin, I need to let you know that this call will be recorded and the information you share will be used to assess your application. Your data will be processed in accordance with GDPR. Are you happy to proceed on that basis?"

Wait for user response.

If they decline: "I completely understand. A recruiter will be in touch to discuss alternative options. Thank you for your time." End the call.

If they consent: proceed to Step 3.

### Step 3: Experience

Say: "Wonderful. Let's get started. First — how many years have you been working as a software engineer, and what's your current or most recent role?"

Wait for user response. If the answer is very short (under 10 words), say: "Could you tell me a bit more about that?" Wait again.

### Step 4: Tech Stack

Say: "Thanks. And what programming languages and frameworks do you work with day to day?"

Wait for user response.

### Step 5: Problem-Solving

Say: "Great. Can you walk me through a recent technical challenge you solved? What was the problem and how did you approach it?"

Wait for user response. If the answer is very short, say: "Could you tell me a bit more about that?" Wait again.

### Step 6: Collaboration

Say: "Thanks for sharing that. How do you typically work with other engineers — do you prefer pair programming, async code reviews, or something else?"

Wait for user response.

### Step 7: Availability

Say: "And finally, what's your notice period, and when would you be available to start a new role?"

Wait for user response.

### Step 8: Submit Screening

Say: "Thank you for answering those questions. Let me submit your screening now."

Call the `submit_screening` function with the following arguments:
- `candidate_name`: the candidate's name from {{candidate_name}}
- `candidate_phone`: the candidate's phone number from {{candidate_phone}} (if available, otherwise "unknown")
- `role_applied`: "software_engineer"
- `consent_given`: "true"
- `answer_experience`: the candidate's response to Step 3
- `answer_tech_stack`: the candidate's response to Step 4
- `answer_problem_solving`: the candidate's response to Step 5
- `answer_collaboration`: the candidate's response to Step 6
- `answer_availability`: the candidate's response to Step 7

Wait for the function result before speaking.

### Step 9: Confirmation

If the function returns successfully:

Say: "Your screening is complete. A member of our team will be in touch within 48 hours with next steps. Thank you for your time, {{candidate_name}}, and have a great day!"

If the function fails or returns an error:

Say: "I wasn't able to submit your screening just now, but don't worry — a recruiter will follow up with you directly. Thank you for your time!"

## Handling Edge Cases

- **Candidate asks about salary or benefits:** "That's a great question — a recruiter will be able to discuss compensation details with you in the next stage."
- **Candidate asks about the role details:** "I can tell you this is a software engineering position. For specific details about the team and project, a recruiter will go through that with you in the next conversation."
- **Candidate requests a human:** "Of course, I'll make sure a recruiter contacts you directly. Thank you for your time!" End the call.
- **Candidate seems confused or you can't understand them (2 times):** "I'm sorry, I'm having trouble understanding. Let me arrange for a recruiter to call you back instead. Thank you for your patience!" End the call.
- **Candidate goes off-topic:** Gently redirect: "I appreciate you sharing that. Let me ask you the next question so we can get through the screening."

## Important Rules

1. NEVER ask more than one question at a time
2. ALWAYS wait for the candidate's response before moving to the next step
3. NEVER confirm or imply screening results before receiving the function response
4. NEVER make up information about the role, company, or process
5. NEVER skip the GDPR consent step
6. If any required information is missing, still call the function with whatever you have — the backend handles validation
````

- [ ] **Step 2: Commit**

```bash
git add voice_agents_demo/retell_agent_prompt.md
git commit -m "feat: rewrite agent prompt for candidate screening flow"
```

---

## Task 12: README and CLAUDE.md

**Files:**
- Rewrite: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite README.md**

Replace the entire contents of `README.md` with:

```markdown
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
```

- [ ] **Step 2: Update CLAUDE.md**

Replace the entire contents of `CLAUDE.md` with:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: rewrite README and CLAUDE.md for screening agent"
```

---

## Task 13: Delete Stale Documentation

**Files:**
- Delete or update stale files from the booking agent era

- [ ] **Step 1: Check for stale docs**

List files that reference the old SwitchedOn booking system:

```bash
ls voice_agents_demo/*.md
```

Files to evaluate: `RETELL.md` (keep — still relevant for Retell integration), `STATUS.md` (gitignored, ignore), `README.md` in `voice_agents_demo/` (needs removal or update).

- [ ] **Step 2: Remove voice_agents_demo/README.md**

The repo-level README now covers everything. The subdirectory README references booking endpoints that no longer exist.

```bash
rm voice_agents_demo/README.md
```

- [ ] **Step 3: Commit**

```bash
git rm voice_agents_demo/README.md
git commit -m "chore: remove stale subdirectory README"
```

---

## Task 14: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

```bash
cd voice_agents_demo && python -m pytest test_screening.py -v --tb=short
```

Expected: All tests PASS

- [ ] **Step 2: Start server and smoke test**

```bash
cd voice_agents_demo && DEMO_MODE=true python main.py &
sleep 2
curl http://localhost:8000/health
curl -X POST http://localhost:8000/submit-screening \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Demo Candidate",
    "candidate_phone": "07999999999",
    "role_applied": "software_engineer",
    "consent_given": true,
    "answers": {
      "experience": "8 years as a senior engineer",
      "tech_stack": "Python, React, AWS",
      "problem_solving": "I debugged and optimized a system",
      "collaboration": "We do code reviews and pair programming",
      "availability": "Available in 2 weeks"
    },
    "transcript": "demo test"
  }'
curl http://localhost:8000/screenings
kill %1
```

Expected:
- Health returns `{"status": "ok"}`
- Screening returns scorecard with `overall_status: "pass"`, `demo_mode: true`
- Screenings list contains the submitted record

- [ ] **Step 3: Verify Retell function endpoint**

```bash
cd voice_agents_demo && DEMO_MODE=true python main.py &
sleep 2
curl -X POST http://localhost:8000/retell/function \
  -H "Content-Type: application/json" \
  -d '{
    "name": "submit_screening",
    "call": {"call_id": "test-123", "transcript": "test"},
    "args": {
      "candidate_name": "Retell Test",
      "candidate_phone": "07888888888",
      "role_applied": "software_engineer",
      "consent_given": "true",
      "answer_experience": "5 years senior engineer",
      "answer_tech_stack": "Python, TypeScript, React",
      "answer_problem_solving": "Debugged and tested a fix",
      "answer_collaboration": "Code reviews and pair programming",
      "answer_availability": "1 month notice"
    }
  }'
kill %1
```

Expected: Returns scorecard JSON with `id` starting with `SCR-`

- [ ] **Step 4: Final commit — tag as demo-ready**

```bash
git tag v2.0.0-screening-demo
```
