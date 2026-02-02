# Known Failure Modes & Mitigations

This document outlines potential system failures, their impact, and the protective measures implemented (or proposed) to mitigate them. Thinking through these failures is critical for a "production-shaped" demo.

---

## 1. Postcode Misheard (High Impact)
- **Symptom**: Customer is booked into a wrong service area, or an engineer is dispatched to an incorrect address.
- **Detection**: Monitor "address correction" keywords in transcripts or backend validation failures.
- **Mitigation**: 
  - **Implemented**: Mandatory NATO phonetic confirmation (e.g., "S for Sierra").
  - **Proposed**: Explicit confirmation step: "I have your address as [Address]. Is that correct?"

## 2. Name Spelling Errors (Medium Impact)
- **Symptom**: Customers cannot be found in the system when they call back or when the engineer arrives.
- **Detection**: High rate of webhook analysis flagging "name recorded incorrectly."
- **Mitigation**:
  - **Implemented**: Agent proactively asks to spell uncommon or complex names.
  - **Proposed**: Phonetic similarity matching (Soundex/Levenshtein) in the backend to match existing customers.

## 3. Backend Timeout / API Failure (Critical)
- **Symptom**: The agent may tell the customer "booking confirmed" while the backend actually failed to write to the database.
- **Detection**: Discrepancy between Retell successful tool calls and record counts in `calls.json`.
- **Mitigation**:
  - **Implemented**: Deterministic `DEMO_MODE` to ensure 100% success during live demos.
  - **Proposed**: Robust retry logic in the orchestration layer and a "degraded mode" prompt where the agent says, "I'm having trouble connecting to the calendar. I've noted your details and a human will call you back to confirm."

## 4. Prompt Hallucinations (Medium Impact)
- **Symptom**: The agent invents new services, incorrect pricing, or makes promises the business cannot keep.
- **Detection**: Manual transcript audit via `QUALITY_MONITORING.md` protocols.
- **Mitigation**:
  - **Implemented**: Single-prompt "Source of Truth" with strict guardrails against fabricating info.
  - **Proposed**: Guardrail models (e.g., NeMo Guardrails) to filter agent responses before they reach the user.

## 5. Latency Spikes (Low/Medium Impact)
- **Symptom**: Awkward silences in the conversation causing the customer to speak over the agent.
- **Detection**: Monitoring "interruption" count and "turn-around time" in Retell Analytics.
- **Mitigation**:
  - **Implemented**: Kept utterances under 12 seconds to minimize processing time.
  - **Proposed**: Transitioning to faster TTS models (e.g., ElevenLabs Turbo) and regionalizing edge deployments.
