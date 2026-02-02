# SwitchedOn Voice Agent — Technical Implementation

This directory contains the core orchestration logic and configuration for the **SwitchedOn London** voice AI system. It serves as the bridge between **Retell AI's** voice platform and the business's scheduling requirements.

---

## Component Architecture

The implementation is designed with an **interface-driven approach**, ensuring clear boundaries between speech processing and business logic.

### 1. Orchestration API (`main.py`)
A FastAPI-based service that handles:
- **Slot Validation**: Ensures the agent has collected all mandatory information (Name, Phone, Service, Time) before committing a booking.
- **Deterministic References**: Generates `SWO-XXXXX` references. In `DEMO_MODE`, these are cryptographically seeded for reproducibility.
- **State Persistence**: Maintains `calls.json`, a structured audit log of every interaction.

### 2. Integration Layer (`webhook_handler.py`)
Handles Retell AI's event-driven callbacks:
- **Mid-Call Tooling**: Processes `/retell/function` requests triggered by the agent's "book_appointment" intent.
- **Lifecycle Webhooks**: Ingests `call_ended` and `call_analyzed` events to capture full transcripts and post-call sentiment.

### 3. Agent Configuration (`retell_agent_prompt.md`)
The authoritative "Single Prompt" that encodes:
- **Business Logic**: Pricing tiers, South West London coverage, and Gas Safe/NICEIC certifications.
- **Conversational Pacing**: NATO phonetics for postcodes, proactive name spelling, and one-question-per-turn constraints.

---

## API Contract

### Booking Attempt (`POST /attempt-booking`)
This is the core business logic endpoint.

**Request Schema:**
```json
{
  "intent": "book",
  "slots": {
    "full_name": "string",
    "phone_number": "string",
    "service_type": "string",
    "postcode": "string (optional)",
    "preferred_times": ["ISO-8601 string"]
  },
  "transcript": "string",
  "confidence": 0.0
}
```

**Response (Success):**
```json
{
  "status": "confirmed",
  "booking_reference": "SWO-12345",
  "scheduled_time": "2026-02-05T10:00:00Z"
}
```

---

## Environment Variables

The system supports the following optional configuration:

### Core Settings
- **`DEMO_MODE`**: Set to `true` for deterministic booking references and guaranteed success (useful for demos and testing).

### Cal.com Integration (Optional)
- **`CAL_API_KEY`**: Your Cal.com API key for real-time calendar integration.
- **`CAL_EVENT_TYPE_ID`**: The Cal.com Event Type ID for SwitchedOn bookings.

When Cal.com credentials are provided, the system will create real bookings via the Cal.com API. If not configured, it falls back to simulated booking logic with an 80% success rate.

**Example:**
```bash
export CAL_API_KEY="cal_live_xxxxxxxxxxxxx"
export CAL_EVENT_TYPE_ID="123456"
export DEMO_MODE="false"
python main.py
```

---

## Testing & Observability

### Simulated Interactions
You can verify the backend logic independently of the voice layer:
```bash
# Health Check
curl http://localhost:8000/health

# Simulate a Successful Booking
curl -X POST http://localhost:8000/attempt-booking -H "Content-Type: application/json" -d @test_payload.json

# Inspect Global Call Logs
curl http://localhost:8000/calls
```

### Observability Standards
Every call record in `calls.json` includes:
- `id`: Unique UUID or Retell `call_id`.
- `transcript`: The raw text of the conversation.
- `escalation_flag`: Boolean indicating if a human transfer was requested.
- `demo_mode`: Boolean flagging if the call was processed under deterministic constraints.

---

## Strategic Documentation
For high-level strategy and deployment procedures, refer to:
- **[SPECIFICATION.md](SPECIFICATION.md)**: Design constraints and authoritative system spec.
- **[ONBOARDING.md](ONBOARDING.md)**: Client onboarding and integration roadmap.
- **[QUALITY_MONITORING.md](QUALITY_MONITORING.md)**: KPI framework and QA tooling.

---

## ⚖️ Quality Bar
This implementation is considered **Demo-Grade** when:
1. A live voice call results in a spoken reference number.
2. The transcript is persisted with 100% fidelity.
3. `DEMO_MODE` provides 1:1 reproducible outcomes for presentations.
