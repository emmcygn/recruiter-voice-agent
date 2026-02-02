# Retell AI Integration Guide

Comprehensive reference for integrating with Retell AI in this project.
Written to avoid repeat research. If you need to know how Retell works, read this first.

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Agent Types](#2-agent-types)
3. [Custom Functions (Mid-Call Tool Use)](#3-custom-functions-mid-call-tool-use)
4. [Post-Call Webhooks](#4-post-call-webhooks)
5. [The Call Object](#5-the-call-object)
6. [Signature Verification](#6-signature-verification)
7. [Prompt Engineering](#7-prompt-engineering)
8. [Agent Configuration Settings](#8-agent-configuration-settings)
9. [Python SDK](#9-python-sdk)
10. [Our Integration Architecture](#10-our-integration-architecture)
11. [Retell Dashboard Setup](#11-retell-dashboard-setup)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Platform Overview

Retell AI is a voice agent platform for building, testing, deploying, and monitoring AI phone agents. It handles:

- **Speech-to-Text (STT)**: Transcribes caller speech in real time
- **LLM Response Generation**: Uses your prompt + an LLM to generate agent responses
- **Text-to-Speech (TTS)**: Speaks the response back to the caller
- **Telephony**: Manages phone numbers, inbound/outbound calls, SIP, DTMF
- **Tool Calling**: Agents can invoke custom functions mid-call (hitting your API)
- **Webhooks**: Notifies your backend about call lifecycle events

We use: **Single Prompt Agent** + **Custom Functions** + **Post-Call Webhooks**.

---

## 2. Agent Types

Retell offers two main architectures:

### Single/Multi-Prompt Agent
- **Single Prompt**: One prompt controls all behavior. Best for simple flows. This is what we use.
- **Multi-Prompt**: Multiple prompts, one per "state". More control, more complexity.

### Conversation Flow Agent
- Visual node-based builder with explicit state transitions
- Better for 3-4+ conditional paths, 5+ tools, or complex variable tracking
- Not what we use (overkill for a booking demo)

**Our choice**: Single Prompt Agent, because the booking flow is linear and one prompt can handle it deterministically.

---

## 3. Custom Functions (Mid-Call Tool Use)

This is how the agent calls our backend **during a live call**.

### How It Works

1. You define a function in the Retell dashboard (name, URL, parameters as JSON Schema)
2. You reference the function by name in your agent prompt
3. During a call, the agent decides to call the function based on conversation context
4. Retell POSTs to your URL with the function args
5. Your backend returns JSON
6. Retell converts the JSON to text and feeds it back to the agent
7. The agent speaks the result to the caller

### Request Format (What Retell Sends You)

```
POST /your-endpoint
Content-Type: application/json
X-Retell-Signature: <encrypted body>
```

```json
{
  "name": "book_appointment",
  "call": {
    "call_id": "abc123",
    "call_type": "phone_call",
    "agent_id": "agent_xyz",
    "transcript": "Agent: ... User: ...",
    "start_timestamp": 1714608475945,
    ...
  },
  "args": {
    "full_name": "Jane Smith",
    "phone_number": "07123456789",
    "service_type": "electrical",
    "preferred_times": "2026-02-05T10:00:00Z"
  }
}
```

Key fields:
- `name` — the function name you registered in the dashboard
- `call` — full call context including real-time transcript up to that moment
- `args` — the arguments extracted by the LLM, matching your JSON Schema

### Response Format (What You Return)

- HTTP status 200-299 = success
- Body: any JSON, string, or buffer (all converted to string for the agent)
- **15,000 character limit** on the response (to avoid overloading the LLM context)

Example response:
```json
{
  "status": "confirmed",
  "booking_reference": "SWO-2EE21",
  "scheduled_time": "2026-02-05T10:00:00Z"
}
```

### Timeout & Retries

- Default timeout: **2 minutes** (configurable)
- Retries: up to **2 times** on failure

### Parameter Definition (JSON Schema)

When registering the function in the dashboard, you define parameters as JSON Schema:

```json
{
  "type": "object",
  "required": ["full_name", "phone_number", "service_type", "preferred_times"],
  "properties": {
    "full_name": { "type": "string", "description": "Customer's full name" },
    "phone_number": { "type": "string", "description": "Customer's phone number" },
    "service_type": { "type": "string", "description": "Type of service needed" },
    "postcode": { "type": "string", "description": "Customer's postcode (optional)" },
    "preferred_times": { "type": "string", "description": "Preferred appointment date and time in ISO-8601 format" }
  }
}
```

You can use `const` values for static data or `{{variable_name}}` for dynamic variables.

---

## 4. Post-Call Webhooks

These fire **after** call lifecycle events. They are NOT for mid-call tool use.

### Event Types

| Event | When | What's Included |
|---|---|---|
| `call_started` | Call connects | Basic call info. Does NOT fire if dial fails. |
| `call_ended` | Call ends (hangup, transfer, error) | Full transcript, timestamps, disconnection reason. No `call_analysis` yet. |
| `call_analyzed` | Post-call analysis completes | Full call object with `call_analysis` field populated. |

### Payload Format

```json
{
  "event": "call_ended",
  "call": {
    "call_id": "abc123",
    "call_type": "phone_call",
    "agent_id": "agent_xyz",
    "from_number": "+447123456789",
    "to_number": "+442012345678",
    "direction": "inbound",
    "call_status": "ended",
    "start_timestamp": 1714608475945,
    "end_timestamp": 1714608491736,
    "duration_ms": 15791,
    "disconnection_reason": "user_hangup",
    "transcript": "Agent: Hello... User: I need...",
    "transcript_object": [
      { "role": "agent", "content": "Hello...", "words": [...] }
    ],
    "transcript_with_tool_calls": [...],
    "recording_url": "https://...",
    "metadata": {},
    "retell_llm_dynamic_variables": {}
  }
}
```

### Webhook Behavior

- Method: **POST**
- Timeout: **10 seconds**
- Retries: up to **3 times** on non-2xx response
- Events fire in order but are **non-blocking** (a failed `call_started` won't prevent `call_ended`)
- Expected response: **2xx status** (204 preferred, 200 works)

### Registration

- **Account-level**: Dashboard > Settings > Webhooks tab (applies to all agents)
- **Agent-level**: Set `webhook_url` on the agent (overrides account-level for that agent)

---

## 5. The Call Object

The `call` object appears in both custom function requests and webhook payloads. Here is the complete schema (from the Get Call API):

### Common Fields (V2CallBase)

| Field | Type | Description |
|---|---|---|
| `call_id` | string | Unique call identifier |
| `agent_id` | string | Associated agent ID |
| `agent_name` | string | Agent name |
| `agent_version` | integer | Agent version number |
| `call_status` | enum | `registered`, `not_connected`, `ongoing`, `ended`, `error` |
| `metadata` | object | Arbitrary storage object |
| `retell_llm_dynamic_variables` | object | Key-value pairs injected into prompts |
| `collected_dynamic_variables` | object | Variables collected during the call (post-call only) |
| `start_timestamp` | integer | Epoch milliseconds |
| `end_timestamp` | integer | Epoch milliseconds |
| `duration_ms` | integer | Call duration |
| `transcript` | string | Plain text transcript |
| `transcript_object` | array | Structured utterances with timestamps |
| `transcript_with_tool_calls` | array | Transcript weaved with tool invocations and results |
| `disconnection_reason` | string | `user_hangup`, `call_transferred`, error codes |
| `recording_url` | string | S3 URL (10-minute or 24-hour expiry depending on signed URL config) |
| `public_log_url` | string | Public debug log URL |
| `call_analysis` | object | Summary, sentiment, success status (only in `call_analyzed` event) |
| `call_cost` | object | Cost breakdown in cents |
| `latency` | object | Metrics: e2e, asr, llm, tts, knowledge_base |
| `data_storage_setting` | enum | `everything`, `everything_except_pii`, `basic_attributes_only` |
| `opt_in_signed_url` | boolean | Signed URL flag |

### Phone-Call-Specific Fields

| Field | Type | Description |
|---|---|---|
| `call_type` | `"phone_call"` | |
| `from_number` | string | Caller number |
| `to_number` | string | Called number |
| `direction` | enum | `inbound` or `outbound` |

### Web-Call-Specific Fields

| Field | Type | Description |
|---|---|---|
| `call_type` | `"web_call"` | |
| `access_token` | string | Web call token |

---

## 6. Signature Verification

Both custom functions and webhooks include an `X-Retell-Signature` header.

### Python Verification

```python
from retell import Retell
import json, os

retell = Retell(api_key=os.environ["RETELL_API_KEY"])

# For POST requests:
is_valid = retell.verify(
    json.dumps(post_data, separators=(",", ":"), ensure_ascii=False),
    api_key=os.environ["RETELL_API_KEY"],
    signature=request.headers.get("X-Retell-Signature")
)

# For GET/DELETE requests (empty body):
is_valid = retell.verify(
    "",
    api_key=os.environ["RETELL_API_KEY"],
    signature=request.headers.get("X-Retell-Signature")
)
```

**Critical**: Use `separators=(",", ":")` and `ensure_ascii=False` when serializing the body. Mismatched serialization = verification failure.

### IP Allowlisting

Retell sends from: **`100.20.5.228`**

### Current Status in Our Code

We do NOT currently verify signatures. For a demo this is acceptable. For production, add verification to both `/retell/function` and `/webhook/retell`.

---

## 7. Prompt Engineering

### Recommended Prompt Structure

Break the prompt into focused sections:

1. **Identity** — Who the agent is, role, company
2. **Style Guardrails** — Tone, brevity, professional constraints
3. **Response Guidelines** — Pacing, confirmation patterns, formatting
4. **Task Instructions** — Step-by-step procedures (numbered steps work best)
5. **Tool Instructions** — When and how to call each function
6. **Failure/Escalation** — What to do when things go wrong

### Key Best Practices

- **Step-based tasks**: Write procedures as numbered steps, not open-ended instructions
- **"Wait for user response"**: Insert explicit pauses between steps to prevent the agent from rushing
- **One question at a time**: Never ask multiple questions in one turn
- **Tool references by exact name**: Always specify exact conditions for when to call a tool
- **Keep responses under 2 sentences** unless explaining something complex
- **Confirm PII**: Always read back phone numbers, names, etc.
- **Spoken formats**: Phone numbers with pauses ("four one five - eight nine two"), times as "Ten AM" not "10:00"

### What NOT to Do

- Don't rely solely on tool descriptions for when to call them
- Don't use a single prompt if you have 5+ tools or 3-4+ conditional branches
- Don't let the agent confirm outcomes before receiving function results

---

## 8. Agent Configuration Settings

Key settings when creating/configuring an agent in the dashboard or via API:

### Voice
- `voice_id` — which voice to use (ElevenLabs, Cartesia, etc.)
- `voice_model` — model variant (e.g., `eleven_turbo_v2`, `sonic-3`)
- `voice_temperature` — stability [0-2], default 1
- `voice_speed` — speech rate [0.5-2], default 1
- `volume` — [0-2], default 1

### Interaction
- `responsiveness` — how quickly agent responds [0-1], default 1
- `interruption_sensitivity` — how easily user can interrupt [0-1], default 1
- `enable_backchannel` — "yeah", "uh-huh" interjections
- `reminder_trigger_ms` — silence before reminder, default 10000ms
- `begin_message_delay_ms` — delay before first message [0-5000ms]

### Audio
- `ambient_sound` — `coffee-shop`, `call-center`, etc.
- `normalize_for_speech` — converts numbers/dates to spoken words
- `denoising_mode` — noise cancellation level

### Speech Recognition
- `language` — default `en-US`, supports 50+ languages + `multi`
- `stt_mode` — `fast` (default), `accurate`, or `custom`
- `boosted_keywords` — words biased for transcription accuracy

### Call Management
- `end_call_after_silence_ms` — default 600000 (10 min)
- `max_call_duration_ms` — default 3600000 (1 hr), max 7200000 (2 hr)
- `webhook_url` — per-agent webhook override

### Post-Call Analysis
- `post_call_analysis_data` — define what to extract (string, enum, boolean, number)
- `post_call_analysis_model` — which LLM to use for analysis (default `gpt-4.1-mini`)
- `analysis_summary_prompt` — guide summary generation
- `analysis_successful_prompt` — define call success criteria

---

## 9. Python SDK

### Install

```bash
pip install retell-sdk
```

### Initialize

```python
from retell import Retell
client = Retell(api_key="YOUR_API_KEY")
```

### Key Operations

```python
# Create agent
agent = client.agent.create(
    response_engine={"llm_id": "llm_xxx", "type": "retell-llm"},
    voice_id="11labs-Adrian",
)

# Get call
call = client.call.retrieve("call_id")

# List calls
calls = client.call.list()

# Create phone call
call = client.call.create_phone_call(
    from_number="+1234567890",
    to_number="+0987654321",
    override_agent_id="agent_xxx",
)

# Verify signature
is_valid = client.verify(body_string, api_key="key", signature="sig")
```

### Error Handling

| Status | Exception |
|---|---|
| 400 | `BadRequestError` |
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` |
| 5xx | `InternalServerError` |

Default: 2 automatic retries on connection errors, 408, 409, 429, 5xx.

---

## 10. Our Integration Architecture

```
                    Retell Platform
                    ┌─────────────────────────┐
                    │  Voice Agent             │
  Caller ──phone──> │  (Single Prompt)         │
                    │                          │
                    │  During call:            │
                    │  ┌──────────────────┐    │
                    │  │ book_appointment  │────┼──POST──> /retell/function
                    │  │ (Custom Function) │<───┼──JSON──  (our backend)
                    │  └──────────────────┘    │
                    │                          │
                    │  After call:             │
                    │  call_ended event  ──────┼──POST──> /webhook/retell
                    │  call_analyzed event ────┼──POST──> /webhook/retell
                    └─────────────────────────┘

Our Backend (FastAPI)
┌──────────────────────────────────────────────┐
│                                              │
│  POST /retell/function                       │
│    → Receives custom function calls          │
│    → Routes by function name                 │
│    → Calls attempt_booking() for bookings    │
│    → Returns result for agent to speak       │
│                                              │
│  POST /webhook/retell                        │
│    → Receives post-call lifecycle events     │
│    → Logs call_ended records with transcript │
│    → Acknowledges all events with 200        │
│                                              │
│  POST /attempt-booking                       │
│    → Core booking logic (also called by      │
│      /retell/function internally)            │
│    → Validates slots, generates reference    │
│    → Persists call record                    │
│                                              │
│  GET /calls                                  │
│    → Returns all stored call records         │
│                                              │
│  GET /health                                 │
│    → Health check                            │
│                                              │
└──────────────────────────────────────────────┘
```

### Data Flow for a Booking

1. Caller talks to the Retell voice agent
2. Agent collects slots (name, phone, service, time)
3. Agent reads back summary, caller confirms
4. Agent calls `book_appointment` custom function
5. Retell POSTs to our `/retell/function` endpoint
6. We validate slots, generate a booking reference, persist the record
7. We return `{"status": "confirmed", "booking_reference": "SWO-XXX", ...}`
8. Retell feeds the response to the agent
9. Agent reads the booking reference and time to the caller
10. Call ends
11. Retell fires `call_ended` webhook to `/webhook/retell`
12. We log the full call record with transcript

---

## 11. Retell Dashboard Setup

After deploying the backend (e.g., via ngrok), configure in Retell:

### Custom Function Registration

1. Go to your agent's configuration
2. Add a Custom Function:
   - **Name**: `book_appointment`
   - **Description**: "Book a service appointment for the customer after confirming all details"
   - **Method**: POST
   - **URL**: `https://<your-ngrok>/retell/function`
   - **Parameters**: (see JSON Schema in section 3)
   - **Timeout**: 30 seconds (default is fine)

### Webhook Registration

1. Go to agent settings (or account-level settings)
2. Set **Webhook URL**: `https://<your-ngrok>/webhook/retell`
3. All events (`call_started`, `call_ended`, `call_analyzed`) will fire to this URL

### Agent Prompt

Paste the contents of `retell_agent_prompt.md` into the agent's prompt field.

### Recommended Agent Settings

- **Voice**: Pick one from the voice library
- **Language**: `en-GB` (London business)
- **Responsiveness**: 0.8-1.0
- **Normalize for speech**: enabled
- **Begin message delay**: 500ms (give caller time to settle)
- **Ambient sound**: `call-center` (optional, adds realism)

---

## 12. Troubleshooting

### Custom function not being called
- Check the function name in your prompt matches the dashboard exactly
- Ensure your prompt has explicit conditions for when to call it
- Test with Retell's "Test Agent" feature first

### Webhook not receiving events
- Verify ngrok is running and URL is correct
- Check Retell dashboard for webhook delivery logs
- Ensure your endpoint returns 2xx within 10 seconds

### Signature verification failing
- Use `separators=(",", ":")` and `ensure_ascii=False` in `json.dumps()`
- Make sure you're using the correct API key (check dashboard)
- For GET/DELETE, verify against an empty string

### Agent speaking before function returns
- Add explicit instructions: "Wait for the function result before speaking"
- Increase function timeout if backend is slow

### Agent asking multiple questions at once
- Add "wait for user response" between steps in the prompt
- Use numbered steps, not paragraph instructions

---

## Source URLs

All research sourced from official Retell documentation:

- Custom Functions: https://docs.retellai.com/build/conversation-flow/custom-function
- Webhook Security: https://docs.retellai.com/features/webhook
- Webhook Overview: https://docs.retellai.com/features/webhook-overview
- Webhook Setup: https://docs.retellai.com/features/register-webhook
- Single Prompt Guide: https://docs.retellai.com/build/single-multi-prompt/write-single-prompt
- Prompt Engineering: https://docs.retellai.com/build/prompt-engineering-guide
- Prompt Situations: https://docs.retellai.com/build/prompt-situation-guide
- Basic Settings: https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings
- Get Call API: https://docs.retellai.com/api-references/get-call
- Create Agent API: https://docs.retellai.com/api-references/create-agent
- Post-Call Analysis: https://docs.retellai.com/features/post-call-analysis-consumption
- Python SDK: https://github.com/RetellAI/retell-python-sdk
- Python SDK (PyPI): https://pypi.org/project/retell-sdk/
- Docs Index: https://docs.retellai.com/llms.txt
