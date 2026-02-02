# Quality Monitoring & Observability Tools

Framework for maintaining and improving the SwitchedOn Voice Agent's performance.

## 1. Core Metrics (KPIs)
- **Booking Completion Rate**: % of calls with "book" intent that result in a confirmed reference.
- **Escalation Rate**: % of calls transferred to a human agent.
- **Average Handle Time (AHT)**: Duration of voice interactions.
- **Slot Confidence**: Accuracy of name, phone, and postcode extraction.

## 2. Monitoring Tools
### Retell AI Dashboard
- **Live Monitoring**: View active calls and latency metrics.
- **Post-Call Analysis**: Automatic sentiment analysis and summary generation.
- **Latency Tracking**: Monitor TTS and LLM response times.

### Backend Orchestration (FastAPI)
- **`calls.json` Log**: Inspect structured data, transcripts, and backend decision logs.
- **Error Tracking**: Monitor `/attempt-booking` failure reasons (e.g., missing slots).

### External Observability (Recommended)
- **LangSmith**: Trace LLM decisions and version-control prompts.
- **Grafana/Prometheus**: Visualize booking trends and system health.

## 3. Human-in-the-loop (HITL) Process
- **Flagged Call Review**: Daily review of calls with "escalate" intent or low confidence scores.
- **Sentiment Triggers**: Automatically alert supervisors when negative sentiment is detected.
- **Transcript Correction**: Use "Name Recorded Wrong" events to fine-tune phonetic aliases in the prompt.

## 4. Automated QA Testing
- **Simulation Suite**: Run batch simulations of common booking scenarios.
- **Regression Testing**: Ensure prompt updates don't break existing successful flows.
