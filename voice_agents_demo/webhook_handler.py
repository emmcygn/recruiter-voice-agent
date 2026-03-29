from fastapi import Request
import json
import uuid
import logging
from datetime import datetime, timezone
from main import app, load_screenings, save_screenings, DEMO_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/webhook/retell")
async def retell_webhook(request: Request):
    """
    Post-call webhook for Retell.
    Logs call_ended events with transcript and metadata.
    """
    body = await request.json()
    event = body.get("event")
    logger.info(f"Retell webhook event={event}: {json.dumps(body, indent=2)}")

    if event == "call_ended":
        call_data = body.get("call", {})
        screenings = load_screenings()
        call_record = {
            "id": f"CALL-{call_data.get('call_id', uuid.uuid4().hex[:8])}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_name": "",
            "candidate_phone": "",
            "role_applied": "",
            "consent_given": False,
            "overall_status": "call_ended",
            "overall_score": 0,
            "scores": {},
            "transcript": call_data.get("transcript", ""),
            "demo_mode": DEMO_MODE,
            "call_metadata": {
                "start_timestamp": call_data.get("start_timestamp"),
                "end_timestamp": call_data.get("end_timestamp"),
                "call_id": call_data.get("call_id"),
            },
        }
        screenings.append(call_record)
        save_screenings(screenings)
        logger.info(f"Logged call_ended for call_id={call_data.get('call_id')}")

    return {"status": "ok", "event": event}


@app.get("/webhook/health")
async def webhook_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "retell-webhook",
    }
