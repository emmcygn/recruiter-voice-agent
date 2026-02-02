from fastapi import Request, HTTPException
import json
import uuid
import logging
from datetime import datetime, timezone
from main import app, load_calls, save_calls, DEMO_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/webhook/retell")
async def retell_webhook(request: Request):
    """
    Post-call webhook for Retell.
    Retell sends event-based payloads:
      {"event": "call_started"|"call_ended"|"call_analyzed", "call": {...}}
    We log the call on call_ended; acknowledge everything else with 200.
    """
    body = await request.json()
    event = body.get("event")
    logger.info(f"Retell webhook event={event}: {json.dumps(body, indent=2)}")

    if event == "call_ended":
        call_data = body.get("call", {})
        calls = load_calls()
        call_record = {
            "id": call_data.get("call_id", str(uuid.uuid4())),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transcript": call_data.get("transcript", ""),
            "intent": "call_ended",
            "slots": {},
            "backend_response": {},
            "success": False,
            "escalation_flag": False,
            "demo_mode": DEMO_MODE,
            "call_metadata": {
                "start_timestamp": call_data.get("start_timestamp"),
                "end_timestamp": call_data.get("end_timestamp"),
                "call_id": call_data.get("call_id"),
            },
        }
        calls.append(call_record)
        save_calls(calls)
        logger.info(f"Logged call_ended for call_id={call_data.get('call_id')}")

    return {"status": "ok", "event": event}


@app.get("/webhook/health")
async def webhook_health():
    """Health check endpoint for webhook monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "retell-webhook",
    }


@app.post("/webhook/test")
async def test_webhook():
    """Test endpoint that simulates a call_ended event."""
    test_body = {
        "event": "call_ended",
        "call": {
            "call_id": "test-webhook-" + uuid.uuid4().hex[:8],
            "transcript": "Test call transcript",
            "start_timestamp": 1714608475945,
            "end_timestamp": 1714608491736,
        },
    }
    # Build a fake Request-like object — just call our handler logic directly
    calls = load_calls()
    call_data = test_body["call"]
    call_record = {
        "id": call_data["call_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transcript": call_data["transcript"],
        "intent": "call_ended",
        "slots": {},
        "backend_response": {},
        "success": False,
        "escalation_flag": False,
        "demo_mode": DEMO_MODE,
        "call_metadata": {
            "start_timestamp": call_data["start_timestamp"],
            "end_timestamp": call_data["end_timestamp"],
            "call_id": call_data["call_id"],
        },
    }
    calls.append(call_record)
    save_calls(calls)

    return {"test_event": test_body, "logged": True}
