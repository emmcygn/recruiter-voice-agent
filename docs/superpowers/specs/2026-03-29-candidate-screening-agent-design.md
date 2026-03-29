# Candidate Screening Voice Agent — Design Spec

> **Date:** 2026-03-29
> **Target demo:** Wave Labs interview, 2026-03-30
> **Approach:** Pivot existing SwitchedOn voice agent repo (Approach A — in-place rewrite)
> **Build time:** ~8-10 hours across 2 days

---

## 1. System Overview

A voice AI agent conducts structured software engineer screening interviews over the phone. The agent asks 5 fixed questions, extracts structured answers, scores the candidate, and persists a full scorecard with transcript.

### Three Layers

1. **Voice Layer (Retell AI)** — Single-prompt agent configured via dashboard. Triggers `submit_screening` custom function mid-call. No Retell SDK/API used programmatically — test calls triggered from Retell dashboard for free.
2. **Orchestration Layer (FastAPI)** — Receives screening submissions, validates, scores via keyword extraction, persists structured scorecards. Exposed via ngrok for Retell to reach.
3. **Persistence Layer** — `screenings.json` flat file. Same pattern as current `calls.json`.

### Live Demo Flow

1. Trigger test call from Retell dashboard
2. Agent greets candidate, states GDPR consent line, asks 5 screening questions
3. After final question, agent calls `submit_screening` custom function → hits backend
4. Backend scores, generates scorecard, returns confirmation to agent
5. Agent thanks candidate, ends call
6. `GET /screenings` returns the JSON scorecard

---

## 2. Screening Questions

Five questions in fixed order:

| # | Category | Question |
|---|---|---|
| 1 | Experience | "How many years have you been working as a software engineer, and what's your current or most recent role?" |
| 2 | Tech Stack | "What programming languages and frameworks do you work with day to day?" |
| 3 | Problem-Solving | "Can you walk me through a recent technical challenge you solved? What was the problem and how did you approach it?" |
| 4 | Collaboration | "How do you typically work with other engineers — do you prefer pair programming, async code reviews, or something else?" |
| 5 | Availability | "What's your notice period, and when would you be available to start a new role?" |

### Why These 5

They map to what high-volume recruitment screens filter on: experience fit, stack match, problem-solving signal, culture fit, and logistics. Short enough for a 3-5 minute call. No gotcha questions that sound awkward spoken aloud.

---

## 3. Scoring Model

Each question gets a 1-5 score and a one-line rationale. Scoring is keyword/pattern-based (deterministic, observable, no LLM API costs).

| Score | Meaning |
|---|---|
| 5 | Strong signal, exceeds expectations |
| 4 | Good signal, meets expectations |
| 3 | Adequate, some gaps |
| 2 | Weak signal, concerns |
| 1 | No usable signal or red flag |

### Overall Status Thresholds

- `pass`: average >= 3.5
- `flag`: average >= 2.5 and < 3.5
- `fail`: average < 2.5

### Scoring Logic Per Question

- **Experience:** Parse years mentioned. 5+ years = 5, 3-4 = 4, 1-2 = 3, <1 or unclear = 2, no signal = 1. Senior/lead/staff title keywords boost by 1.
- **Tech Stack:** Count recognized languages/frameworks against a target list (Python, TypeScript, JavaScript, React, Node, PostgreSQL, AWS, Docker, Kubernetes, Go, Java, C#, Ruby, Rust). 5+ matches = 5, 3-4 = 4, 2 = 3, 1 = 2, 0 = 1.
- **Problem-Solving:** Look for methodology signals: "debugged", "profiled", "tested", "refactored", "scaled", "optimized", "root cause", "trade-off". 4+ signals = 5, 3 = 4, 2 = 3, 1 = 2, 0 = 1.
- **Collaboration:** Look for collaboration keywords: "pair", "review", "PR", "code review", "stand-up", "retro", "async", "sync", "mentor", "team". 3+ = 5, 2 = 4, 1 = 3, vague = 2, nothing = 1.
- **Availability:** Parse notice period. Immediate/1-2 weeks = 5, 1 month = 4, 2 months = 3, 3+ months = 2, unclear = 1.

### DEMO_MODE Behavior

When `DEMO_MODE=true`:
- Scoring bypassed — returns hardcoded "ideal candidate" scorecard
- All scores set to 4-5
- Overall status always `pass`
- Screening ID is deterministic (MD5-seeded from candidate name)
- Same input always produces identical output

---

## 4. API Contract

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST /retell/function` | Retell custom function handler | Routes `submit_screening` calls from voice agent |
| `POST /submit-screening` | Core screening logic | Validates, scores, persists scorecard |
| `GET /screenings` | List all screenings | Returns all persisted scorecards |
| `GET /screenings/{id}` | Single scorecard | Returns one screening by ID |
| `GET /health` | Health check | Unchanged |
| `POST /webhook/retell` | Post-call webhook | Logs transcript on `call_ended` |

### Request Model — `ScreeningSubmission`

```json
{
  "candidate_name": "string (required)",
  "candidate_phone": "string (required)",
  "role_applied": "software_engineer",
  "consent_given": true,
  "answers": {
    "experience": "free-text answer string",
    "tech_stack": "free-text answer string",
    "problem_solving": "free-text answer string",
    "collaboration": "free-text answer string",
    "availability": "free-text answer string"
  },
  "transcript": "string"
}
```

### Response Model — `ScreeningScorecard`

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "candidate_name": "string",
  "candidate_phone": "string",
  "role_applied": "software_engineer",
  "consent_given": true,
  "overall_status": "pass | flag | fail",
  "overall_score": 4.2,
  "scores": {
    "experience": { "score": 5, "rationale": "5 years, senior-level role" },
    "tech_stack": { "score": 4, "rationale": "4 matching technologies" },
    "problem_solving": { "score": 4, "rationale": "Clear methodology, 3 signals" },
    "collaboration": { "score": 3, "rationale": "1 collaboration keyword" },
    "availability": { "score": 5, "rationale": "4 weeks notice" }
  },
  "transcript": "string",
  "demo_mode": false
}
```

### Consent Rejection Response

When `consent_given` is `false`:

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "candidate_name": "string",
  "candidate_phone": "string",
  "role_applied": "software_engineer",
  "consent_given": false,
  "overall_status": "rejected",
  "overall_score": 0,
  "scores": {},
  "transcript": "string",
  "demo_mode": false
}
```

### Retell Custom Function Interface

Retell sends flat key-value args. The `/retell/function` handler reassembles them:

```json
{
  "name": "submit_screening",
  "call": { "call_id": "...", "transcript": "..." },
  "args": {
    "candidate_name": "Jane Smith",
    "candidate_phone": "07123456789",
    "role_applied": "software_engineer",
    "consent_given": "true",  // string from Retell — backend parses to boolean
    "answer_experience": "5 years, senior dev at...",
    "answer_tech_stack": "Python, TypeScript, React...",
    "answer_problem_solving": "We had a scaling issue...",
    "answer_collaboration": "Mostly async PRs...",
    "answer_availability": "4 weeks notice..."
  }
}
```

---

## 5. Voice Agent Prompt Design

### Identity

"You are a talent screening assistant for a technology recruitment agency. Your role is to conduct a brief, structured phone screening for software engineering candidates."

### Call Flow (Numbered Steps)

1. Greet candidate by name (via Retell dynamic variable `{{candidate_name}}`)
2. State purpose: "I'm calling to conduct a brief screening interview for the software engineer role you applied for"
3. GDPR consent: "This call will be recorded and assessed. Your data will be processed in accordance with GDPR. Are you happy to proceed?"
4. If no consent → thank them, end call
5. Ask each of the 5 questions in order, one per turn, wait for response
6. After all 5 answers collected: "Thank you, let me submit your screening now" → call `submit_screening`
7. On success → "Your screening is complete. A member of our team will be in touch within 48 hours."
8. On failure → "I wasn't able to submit your screening. A recruiter will follow up with you directly."
9. Thank and end call

### Behavioral Constraints

- One question per turn, wait for response before proceeding
- If candidate gives a very short answer, probe once: "Could you tell me a bit more about that?"
- Never ask multiple questions at once
- Keep responses under 2 sentences
- Salary/benefits questions: "A recruiter will be able to discuss that with you in the next stage"
- Human request: "Of course, I'll make sure a recruiter contacts you directly" → end call
- After 2 misunderstandings → offer to have a recruiter call back

### Retell Dashboard Configuration

- **Custom Function:** name `submit_screening`, POST to `https://<ngrok>/retell/function`
- **Parameters (JSON Schema):** `candidate_name` (string, required), `candidate_phone` (string, required), `role_applied` (string, required), `consent_given` (string, required), `answer_experience` (string, required), `answer_tech_stack` (string, required), `answer_problem_solving` (string, required), `answer_collaboration` (string, required), `answer_availability` (string, required)
- **Webhook URL:** `https://<ngrok>/webhook/retell`
- **Language:** `en-GB`
- **Dynamic variable:** `candidate_name` (set per-call or defaults to "there")

---

## 6. File Changes

| File | Action | What changes |
|---|---|---|
| `main.py` | **Rewrite** | New Pydantic models, new endpoints, keyword scoring engine, DEMO_MODE determinism |
| `retell_agent_prompt.md` | **Rewrite** | 5-question screening prompt with GDPR opening |
| `cal_client.py` | **Delete** | Not needed for screening |
| `webhook_handler.py` | **Update** | Update imports if model names change, otherwise minimal |
| `requirements.txt` | **Update** | Add `pytest` and `pytest-asyncio` for testing |
| `test_screening.py` | **Create** | 13 unit tests |
| `README.md` | **Rewrite** | New repo narrative, API docs, extension points |
| `CLAUDE.md` | **Update** | Reflect new architecture |
| `screenings.json` | **Runtime** | Created at runtime, gitignored |

---

## 7. Testing Strategy

### Unit Tests (pytest, no Retell dependency)

| # | Test Name | What It Validates | Success Criteria |
|---|---|---|---|
| 1 | `test_health` | Health endpoint | HTTP 200, `{"status": "ok"}` |
| 2 | `test_submit_screening_valid` | Happy path | HTTP 200, scorecard has all 5 scores, ID format `SCR-XXXXX`, status is pass/flag/fail |
| 3 | `test_submit_screening_missing_fields` | Missing required fields | HTTP 422, no scorecard persisted |
| 4 | `test_submit_screening_no_consent` | `consent_given: false` | HTTP 200, `overall_status: "rejected"`, no scores, reason indicates no consent |
| 5 | `test_scoring_pass` | High-quality answers | Average >= 3.5, `overall_status: "pass"` |
| 6 | `test_scoring_flag` | Mixed answers | Average >= 2.5 and < 3.5, `overall_status: "flag"` |
| 7 | `test_scoring_fail` | Weak answers | Average < 2.5, `overall_status: "fail"` |
| 8 | `test_demo_mode_deterministic` | DEMO_MODE consistency | Same input twice → identical scores, identical ID |
| 9 | `test_screenings_list` | `GET /screenings` | Returns list containing submitted screening |
| 10 | `test_screenings_get_by_id` | `GET /screenings/{id}` | Returns correct scorecard; 404 for bad ID |
| 11 | `test_retell_function_routing` | `/retell/function` with `submit_screening` | Routes correctly, returns scorecard |
| 12 | `test_retell_function_unknown` | `/retell/function` with bad name | Returns error, no side effects |
| 13 | `test_webhook_call_ended` | Webhook persistence | `call_ended` event persisted with metadata |

### Integration Test (Manual, Live Demo Rehearsal)

| Step | Action | Success Criteria |
|---|---|---|
| 1 | Start server `DEMO_MODE=true` | `/health` returns ok |
| 2 | Trigger test call from Retell dashboard | Agent greets, states GDPR line |
| 3 | Answer all 5 questions | Agent waits between questions, probes short answers |
| 4 | Agent submits screening | `submit_screening` fires, backend logs request |
| 5 | Agent reads confirmation | Speaks overall status and next-steps |
| 6 | Call ends | `call_ended` webhook fires, transcript logged |
| 7 | `curl GET /screenings` | Scorecard with all 5 scores, transcript, overall status |

### Overall Demo Success Criteria

1. End-to-end call completes without errors
2. Scorecard contains structured per-question scores with rationales
3. DEMO_MODE produces deterministic, repeatable results
4. Total call duration under 5 minutes
5. No hallucinated data — all scorecard fields trace to what was said

---

## 8. Extension Points (Documented, Not Built)

### GDPR Consent Agent

Outbound call to candidates in the pipeline to collect explicit opt-in for data retention. Agent reads a consent script, records yes/no, persists consent record with timestamp.

- Retell function: `submit_consent`
- Endpoint: `POST /submit-consent`
- Model: `ConsentRecord` (candidate_name, candidate_phone, consent_given, timestamp, transcript)

### No-Show Confirmation Agent

Day-before outbound call to confirm interview attendance. Agent confirms date/time/location, offers rescheduling, flags no-show risk.

- Retell function: `submit_confirmation`
- Endpoint: `POST /submit-confirmation`
- Model: `ConfirmationRecord` (candidate_name, interview_date, confirmed, reschedule_requested, transcript)

### Architecture Note

The `/retell/function` endpoint routes by function name. Adding new agent modes requires: new Retell prompt in dashboard, new function handler in the router, new Pydantic models. Same backend, same persistence pattern.

---

## 9. Out of Scope

- Retell SDK/API usage (no programmatic calls, dashboard only)
- LLM-based scoring (keyword extraction only, deterministic)
- Database (flat JSON file persistence)
- Authentication/authorization on API endpoints
- Retell signature verification
- Frontend/UI
- Cal.com or any calendar integration
- SMS/email notifications
- Connection to talent-tool-mvp codebase (verbal narrative only)
