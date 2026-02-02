# Quality Monitoring & Observability Tools

Framework for maintaining and improving the SwitchedOn Voice Agent's performance across different client tiers.

---

## 1. Core Metrics (KPIs)
- **Booking Completion Rate**: % of calls with "book" intent that result in a confirmed reference.
- **Escalation Rate**: % of calls transferred to a human agent.
- **Average Handle Time (AHT)**: Duration of voice interactions.
- **Slot Confidence**: Accuracy of name, phone, and postcode extraction.

### Red Flags to Monitor (Vigilance Thresholds)
- **Escalation Rate > 15%**: Prompt instructions are unclear or agent is misinterpreting edge cases.
- **Booking Completion < 60%**: Technical integration issues or mandatory slot-filling friction.
- **AHT > 4 minutes**: Agent is being too verbose or getting stuck in loops.

---

## 2. Tool Selection Framework

### For Early-Stage Clients (< 100 calls/day)
- **Retell Dashboard** + **calls.json**: Provides essential visibility without additional vendor overhead.
- **Why**: Minimizes onboarding friction and focuses on immediate time-to-value.

### For Scale Clients (> 500 calls/day)
- **LangSmith**: Trace complex LLM decision-making and version-control prompts.
- **Grafana/Prometheus**: Real-time alerting on technical booking failures (4xx/5xx).
- **Why**: Justifies investment with volume and enables proactive support before the client notices issues.

---

## 3. Monitoring Infrastructure

### Retell AI Dashboard
- **Live Monitoring**: View active calls and latency metrics.
- **Post-Call Analysis**: Automatic sentiment analysis and summary generation.

### Backend Orchestration (FastAPI)
- **`calls.json` Log**: Inspect structured data, transcripts, and backend decision logs.
- **Error Tracking**: Monitor `/attempt-booking` failure reasons (e.g., missing slots).

---

## 4. Human-in-the-loop (HITL) Process
- **Flagged Call Review**: Daily review of calls with "escalate" intent or low confidence scores.
- **Sentiment Triggers**: Automatically alert supervisors when negative sentiment is detected.
- **Transcript Correction**: Use "Name Recorded Wrong" events to fine-tune phonetic aliases in the prompt.

---

## 5. Automated QA Testing
- **Simulation Suite**: Run batch simulations of common booking scenarios (see `demo_simulator.py`).
- **Regression Testing**: Ensure prompt updates don't break existing successful flows.
