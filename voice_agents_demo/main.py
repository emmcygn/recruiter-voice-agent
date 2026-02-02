from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid
from datetime import datetime, timezone
import os
import random
import hashlib
import logging
from cal_client import CalClient

logger = logging.getLogger(__name__)

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

app = FastAPI(title="SwitchedOn Booking API", version="1.0.0")
cal_client = CalClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BookingSlots(BaseModel):
    full_name: str
    phone_number: str
    service_type: str
    postcode: Optional[str] = None
    preferred_times: List[str]

class BookingRequest(BaseModel):
    intent: str
    slots: BookingSlots
    transcript: str
    confidence: float

class BookingResponse(BaseModel):
    status: str
    booking_reference: Optional[str] = None
    scheduled_time: Optional[str] = None
    reason: Optional[str] = None

class CallRecord(BaseModel):
    id: str
    timestamp: str
    transcript: str
    intent: str
    slots: dict
    backend_response: dict
    success: bool
    escalation_flag: bool = False
    demo_mode: bool = False
    call_metadata: Optional[dict] = None

DATA_FILE = "calls.json"

def load_calls():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_calls(calls):
    with open(DATA_FILE, 'w') as f:
        json.dump(calls, f, indent=2)

def generate_booking_reference(seed: str = ""):
    if DEMO_MODE and seed:
        hash_hex = hashlib.md5(seed.encode()).hexdigest()[:5].upper()
        return f"SWO-{hash_hex}"
    return f"SWO-{uuid.uuid4().hex[:5].upper()}"

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/calls", response_model=List[CallRecord])
async def get_calls():
    calls = load_calls()
    return calls

@app.post("/attempt-booking", response_model=BookingResponse)
async def attempt_booking(request: BookingRequest):
    calls = load_calls()
    
    # Validate required slots
    required_slots = ["full_name", "phone_number", "service_type"]
    missing_slots = [slot for slot in required_slots if not getattr(request.slots, slot, None)]
    
    if missing_slots:
        response = {
            "status": "unavailable",
            "reason": f"Missing required information: {', '.join(missing_slots)}"
        }
    elif not request.slots.preferred_times:
        response = {
            "status": "unavailable", 
            "reason": "No preferred time provided"
        }
    else:
        if DEMO_MODE:
            # Deterministic: always succeed in demo mode
            seed = f"{request.slots.full_name}-{request.slots.preferred_times[0]}"
            booking_ref = generate_booking_reference(seed=seed)
            scheduled_time = request.slots.preferred_times[0]
            response = {
                "status": "confirmed",
                "booking_reference": booking_ref,
                "scheduled_time": scheduled_time
            }
        else:
            # Try Cal.com integration if configured
            if cal_client.api_key and cal_client.event_type_id:
                # Generate placeholder email from phone number if not provided
                email = f"{request.slots.phone_number.replace(' ', '')}@placeholder.com"
                scheduled_time = request.slots.preferred_times[0]

                cal_booking_uid = await cal_client.create_booking(
                    full_name=request.slots.full_name,
                    email=email,
                    start_time=scheduled_time,
                    phone=request.slots.phone_number
                )

                if cal_booking_uid:
                    # Cal.com booking successful
                    response = {
                        "status": "confirmed",
                        "booking_reference": f"SWO-{cal_booking_uid[:5].upper()}",
                        "scheduled_time": scheduled_time
                    }
                else:
                    # Cal.com booking failed, fall back to unavailable
                    response = {
                        "status": "unavailable",
                        "reason": "Unable to confirm booking at requested time"
                    }
            else:
                # No Cal.com configured - simulate booking logic with 80% success rate
                if random.random() > 0.2:
                    booking_ref = generate_booking_reference()
                    scheduled_time = request.slots.preferred_times[0]
                    response = {
                        "status": "confirmed",
                        "booking_reference": booking_ref,
                        "scheduled_time": scheduled_time
                    }
                else:
                    response = {
                        "status": "unavailable",
                        "reason": "No availability at requested times"
                    }

    # Store call record
    call_record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transcript": request.transcript,
        "intent": request.intent,
        "slots": request.slots.model_dump(),
        "backend_response": response,
        "success": response["status"] == "confirmed",
        "escalation_flag": request.intent == "escalate",
        "demo_mode": DEMO_MODE
    }
    
    calls.append(call_record)
    save_calls(calls)
    
    return BookingResponse(**response)

@app.post("/retell/function")
async def retell_custom_function(request: Request):
    """
    Retell Custom Function handler.
    Called during a live call when the agent invokes a tool.
    Retell sends: {"name": "...", "call": {...}, "args": {...}}
    We return JSON that Retell relays to the agent as text.
    """
    body = await request.json()
    logger.info(f"Retell custom function call: {json.dumps(body, indent=2)}")

    fn_name = body.get("name")
    args = body.get("args", {})
    call_info = body.get("call", {})

    if fn_name != "book_appointment":
        return {"error": f"Unknown function: {fn_name}"}

    # Build a BookingRequest from the function args
    preferred_times_raw = args.get("preferred_times", "")
    # Retell may send preferred_times as a comma-separated string; split and clean
    if isinstance(preferred_times_raw, str):
        parts = [t.strip() for t in preferred_times_raw.split(",") if t.strip()]
        preferred_times = parts if parts else []
    else:
        preferred_times = preferred_times_raw

    booking_request = BookingRequest(
        intent="book",
        slots={
            "full_name": args.get("full_name", ""),
            "phone_number": args.get("phone_number", ""),
            "service_type": args.get("service_type", ""),
            "postcode": args.get("postcode"),
            "preferred_times": preferred_times,
        },
        transcript=call_info.get("transcript", ""),
        confidence=0.9,
    )

    response = await attempt_booking(booking_request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
