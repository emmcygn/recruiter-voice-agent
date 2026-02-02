# Live Demo Playbook - SwitchedOn Voice Agent

A structured guide for conducting high-impact live demonstrations for prospective clients and stakeholders.

---

## Pre-Demo Checklist (15 min before)
- [ ] **Environment**: Ensure `DEMO_MODE=true` is enabled in your environment variables.
- [ ] **Backend**: Verify `main.py` is running and accessible (`curl http://localhost:8000/health`).
- [ ] **Clean Slate**: Clear `calls.json` or move it to a backup to ensure a clean demo history.
- [ ] **Connection**: Test the Retell phone number/web call once to ensure no latency issues on your current network.

---

## Demo Script (10 Minutes)

### Act 1: The Problem (2 min)
- **Context**: "Every missed call is a missed appointment. SwitchedOn London was losing 25% of their late-night and weekend leads to voicemail."
- **The Gap**: Traditional IVRs are frustrating. Human call centers are expensive.

### Act 2: The Solution (5 min)
**Live Call Demonstration**:
1. **The Greeting**: Call the number. Show how the agent identifies as the "SwitchedOn Assistant."
2. **The Interaction**: Request a "plumbing service for next Tuesday."
3. **The Guardrails**: Provide a tricky name or postcode. Show NATO phonetic confirmation in action.
4. **The Commitment**: Confirm the summary. Listen for the real-time booking reference (e.g., `SWO-XXXXX`).

### Act 3: The Proof (3 min)
- **Structured Data**: Open the `/calls` endpoint or show `calls.json`.
- **Visibility**: Point out the full transcript, extracted slots, and the backend success flag.
- **Scalability**: Mention that this same data is ready to be pushed to Jobber, ServiceM8, or any custom CRM.

---

## Recovery Procedures (The "SE" Safety Net)

- **If the Call Drops**: "As with any live telecom demo, signal fluctuations happen. Let's switch to the **Demo Simulator** to show you the logic layer without the phone line." (Run `python demo_simulator.py`).
- **If the Agent Hallucinates**: "Great catch. This is precisely why we implement **Shadow Mode** during Week 4 of onboarding—to catch and refine these edge cases before full rollout."
- **If Backend Latency occurs**: "We're currently running on a demo-tier server. In production, we utilize regionalized edge deployment to keep latency under 800ms."

---

## Conclusion
- Re-emphasize: **"Reliability over Breadth."**
- Re-iterate: **"The backend is the source of truth."**
