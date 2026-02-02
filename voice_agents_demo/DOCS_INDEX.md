# Documentation & Reference Index

Quick-access index of all documentation, both local and external.
Use this to find things fast without re-searching.

---

## Local Project Files

| File | Purpose |
|---|---|
| `RETELL.md` | Comprehensive Retell AI integration guide (custom functions, webhooks, SDK, prompt engineering) |
| `DOCS_INDEX.md` | This file — documentation index |
| `retell_agent_prompt.md` | The single prompt used by the Retell voice agent |
| `main.py` | FastAPI backend: booking logic, custom function endpoint, models |
| `webhook_handler.py` | Post-call webhook handler for Retell events |
| `README.md` | Project overview, quick start, architecture summary |
| `STATUS.md` | Current implementation status and test results |
| `truth.md` | Original scaffolding specification |
| `requirements.txt` | Python dependencies |
| `calls.json` | Persisted call records (runtime data) |

---

## Retell AI Official Documentation

### Getting Started
| Topic | URL |
|---|---|
| Introduction | https://docs.retellai.com/general/introduction |
| Quick Start (5 min) | https://docs.retellai.com/get-started/quick-start |
| Full Docs Index (llms.txt) | https://docs.retellai.com/llms.txt |
| Changelog | https://www.retellai.com/changelog |

### Agent Building
| Topic | URL |
|---|---|
| Single/Multi-Prompt Overview | https://docs.retellai.com/build/single-multi-prompt/prompt-overview |
| Write a Single Prompt | https://docs.retellai.com/build/single-multi-prompt/write-single-prompt |
| Write a Multi-Prompt Agent | https://docs.retellai.com/build/single-multi-prompt/write-multi-prompt |
| Configure Basic Settings | https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings |
| Prompt Engineering Guide | https://docs.retellai.com/build/prompt-engineering-guide |
| Situation-Specific Prompt Guide | https://docs.retellai.com/build/prompt-situation-guide |
| Conversation Flow Overview | https://docs.retellai.com/build/conversation-flow |

### Custom Functions (Mid-Call Tool Use)
| Topic | URL |
|---|---|
| Custom Function Docs | https://docs.retellai.com/build/conversation-flow/custom-function |

### Webhooks
| Topic | URL |
|---|---|
| Webhook Overview | https://docs.retellai.com/features/webhook-overview |
| Webhook Security & Verification | https://docs.retellai.com/features/webhook |
| Register Webhook (Setup Guide) | https://docs.retellai.com/features/register-webhook |
| Inbound Call Webhook | https://docs.retellai.com/features/inbound-call-webhook |

### Post-Call Analysis
| Topic | URL |
|---|---|
| Consume Analysis Data | https://docs.retellai.com/features/post-call-analysis-consumption |

### API Reference
| Topic | URL |
|---|---|
| Create Voice Agent | https://docs.retellai.com/api-references/create-agent |
| List Voice Agents | https://docs.retellai.com/api-references/list-agents |
| Get Call | https://docs.retellai.com/api-references/get-call |
| Create Phone Call | https://docs.retellai.com/api-references/create-phone-call |
| Create Web Call | https://docs.retellai.com/api-references/create-web-call |
| Create Retell LLM | https://docs.retellai.com/api-references/create-retell-llm |
| Create Chat Agent | https://docs.retellai.com/api-references/create-chat-agent |

### SDKs
| Topic | URL |
|---|---|
| Python SDK (GitHub) | https://github.com/RetellAI/retell-python-sdk |
| Python SDK (PyPI) | https://pypi.org/project/retell-sdk/ |
| TypeScript SDK (GitHub) | https://github.com/RetellAI/retell-typescript-sdk |
| Custom LLM Python Demo | https://github.com/RetellAI/retell-custom-llm-python-demo |

### Telephony & Deployment
| Topic | URL |
|---|---|
| Outbound Calls | https://docs.retellai.com/make-receive-phone-call/outbound |
| Inbound Calls | https://docs.retellai.com/make-receive-phone-call/inbound |
| Web Call Integration | https://docs.retellai.com/make-receive-phone-call/web-call |

---

## Key Technical Facts (Quick Reference)

### Custom Function Request Shape
```json
{
  "name": "function_name",
  "call": { "call_id": "...", "transcript": "...", ... },
  "args": { ... }
}
```
- Response: 200-299, any JSON (capped at 15,000 chars)
- Timeout: 2 min default, up to 2 retries

### Webhook Payload Shape
```json
{
  "event": "call_started" | "call_ended" | "call_analyzed",
  "call": { "call_id": "...", "transcript": "...", ... }
}
```
- Timeout: 10 seconds, up to 3 retries
- Expected response: 2xx

### Signature Header
- Header: `X-Retell-Signature`
- Verify with: `retell.verify(json.dumps(body, separators=(",",":"), ensure_ascii=False), api_key, signature)`
- Retell IP: `100.20.5.228`

### Our Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/calls` | List all call records |
| POST | `/attempt-booking` | Direct booking API (original) |
| POST | `/retell/function` | Retell custom function handler (mid-call) |
| POST | `/webhook/retell` | Retell post-call webhook handler |
| GET | `/webhook/health` | Webhook health check |
| POST | `/webhook/test` | Simulate a call_ended webhook |

### Our book_appointment Function Schema
```json
{
  "type": "object",
  "required": ["full_name", "phone_number", "service_type", "preferred_times"],
  "properties": {
    "full_name": { "type": "string" },
    "phone_number": { "type": "string" },
    "service_type": { "type": "string" },
    "postcode": { "type": "string" },
    "preferred_times": { "type": "string" }
  }
}
```

### Python Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
```

Optional (for signature verification):
```
retell-sdk
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DEMO_MODE` | `"false"` | When `"true"`: deterministic booking refs, 100% success rate, records tagged `demo_mode=true` |
| `RETELL_API_KEY` | (none) | Required for signature verification (not currently implemented) |

---

## Testing Cheat Sheet

```bash
# Start server
DEMO_MODE=true python -c "import uvicorn; import main; import webhook_handler; uvicorn.run(main.app, host='0.0.0.0', port=8000)"

# Test custom function (booking)
curl -X POST http://localhost:8000/retell/function \
  -H "Content-Type: application/json" \
  -d '{"name":"book_appointment","call":{"call_id":"test-123","transcript":"test"},"args":{"full_name":"Jane Smith","phone_number":"07123456789","service_type":"electrical","preferred_times":"2026-02-05T10:00:00Z"}}'

# Test webhook (call ended)
curl -X POST http://localhost:8000/webhook/retell \
  -H "Content-Type: application/json" \
  -d '{"event":"call_ended","call":{"call_id":"test-123","transcript":"full transcript","start_timestamp":1714608475945,"end_timestamp":1714608491736}}'

# Test webhook (call started — just acknowledged)
curl -X POST http://localhost:8000/webhook/retell \
  -H "Content-Type: application/json" \
  -d '{"event":"call_started","call":{"call_id":"test-456"}}'

# Check stored records
curl http://localhost:8000/calls

# Health check
curl http://localhost:8000/health
```
