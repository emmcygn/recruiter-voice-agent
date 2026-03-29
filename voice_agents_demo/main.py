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
    score_work_preference,
    score_availability,
    score_current_salary,
    score_target_salary,
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
    work_preference: str
    availability: str
    current_salary: str
    target_salary: str


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
            "overall_score": 4.9,
            "scores": {
                "experience": {"score": 5, "rationale": "Senior-level, 5+ years"},
                "tech_stack": {"score": 5, "rationale": "5+ matching technologies"},
                "problem_solving": {"score": 4, "rationale": "Clear methodology described"},
                "work_preference": {"score": 5, "rationale": "Prefers hybrid, flexible"},
                "availability": {"score": 5, "rationale": "Available immediately"},
                "current_salary": {"score": 5, "rationale": "Current salary: £85,000"},
                "target_salary": {"score": 5, "rationale": "Target floor salary: £95,000"},
            },
            "transcript": submission.transcript,
            "demo_mode": True,
        }
    else:
        scores = {
            "experience": score_experience(submission.answers.experience),
            "tech_stack": score_tech_stack(submission.answers.tech_stack),
            "problem_solving": score_problem_solving(submission.answers.problem_solving),
            "work_preference": score_work_preference(submission.answers.work_preference),
            "availability": score_availability(submission.answers.availability),
            "current_salary": score_current_salary(submission.answers.current_salary),
            "target_salary": score_target_salary(submission.answers.target_salary),
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
                "work_preference": args.get("answer_work_preference", ""),
                "availability": args.get("answer_availability", ""),
                "current_salary": args.get("answer_current_salary", ""),
                "target_salary": args.get("answer_target_salary", ""),
            },
            transcript=call_info.get("transcript", ""),
        )
        return await submit_screening(submission)

    return {"error": f"Unknown function: {fn_name}"}


# Import webhook_handler to register its routes on the app
import webhook_handler  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
