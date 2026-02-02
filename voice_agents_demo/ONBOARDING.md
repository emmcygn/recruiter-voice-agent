# Customer Onboarding Process - SwitchedOn Voice AI

This document outlines the standard procedure for onboarding a new service business to the SwitchedOn Voice platform, optimized for transparency and risk mitigation.

---

## 0. Pre-Discovery Qualification (Before Engagement)
- **Use Case Validation**: Is voice AI appropriate for this specific workflow? (e.g., appointment booking vs. complex parts diagnosis).
- **Volume Assessment**: Does the call volume justify the automation investment?
- **Technical Readiness**: Does the client have reliable APIs (CRM/Calendar) for integration?
- **Budget Alignment**: Can the client afford the 4-week implementation and ongoing usage fees?

---

## 1. Discovery & Requirements (Week 1)
- **Success Criteria Definition**: Define metrics for success (e.g., >80% Booking Completion, <10% Transfer-to-Human).
- **Stakeholder Map**: Identify key partners in IT, Operations, and Finance for approval and access.
- **Risk Assessment**: Identify potential blockers (e.g., regional accents, industry-specific jargon like "Gas Safe" vs. "Boiler Service").
- **Service Mapping**: Catalogue all services, pricing tiers, and exclusion zones.
- **Integration Audit**: Finalize target CRM or Calendar system (e.g., Cal.com, Jobber, ServiceM8).

---

## 2. Agent Design (Week 2)
- **Prompt Engineering**: Draft the "Single Prompt" personality and rules.
- **Tone & Voice Selection**: Choose appropriate accent and latency settings.
- **Function Mapping**: Define the JSON schema for backend tool calls.

---

## 3. Technical Integration (Week 2-3)
- **Backend Setup**: Configure the orchestration API (FastAPI) to bridge Retell and the CRM.
- **Validation Logic**: Implement rules for "booking slots" (e.g., postcode validation).
- **Webhook Configuration**: Set up post-call logging for transcript ingestion.

---

## 4. Testing & QA (Week 3)
- **Adversarial Testing**: Pressure test for hallucinations and edge cases.
- **NATO Phonetic Validation**: Ensure postcode and name capture accuracy.
- **Integration Test**: Verify end-to-end data flow from voice -> backend -> CRM.

---

## 5. Deployment (Week 4)
- **Shadow Mode**: Deploy as an option on the phone tree (e.g., "Press 1 to try our AI assistant").
- **Closed Beta**: Direct a small percentage of calls to the agent.
- **Full Rollout**: 24/7 deployment with human-handover fallback.

---

## 6. Continuous Improvement
- **Weekly Review**: Manually audit low-confidence calls and update the prompt.
- **Metric Tracking**: Monitor CSAT and Booking Completion Rate against defined success criteria.
