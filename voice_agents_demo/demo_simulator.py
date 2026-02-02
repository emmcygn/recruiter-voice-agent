"""
demo_simulator.py - Interactive SwitchedOn Voice Agent Simulation

This script allows you to "experience" the SwitchedOn London voice agent booking flow 
via a text interface. It communicates directly with the local FastAPI backend, 
demonstrating the logic layer without requiring Retell AI credentials.

Usage:
1. Ensure the backend is running: python main.py
2. Run this simulator: python demo_simulator.py
"""

import httpx
import asyncio
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

async def check_health():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False

async def simulate_booking():
    print("\n--- SwitchedOn London: Interactive Demo Simulator ---")
    print("Type your 'speech' as if you were talking to the voice agent.")
    print("(This simulates the Retell AI -> Backend webhook flow)\n")

    if not await check_health():
        print("Error: Backend is not running on http://localhost:8000")
        print("Please run 'python main.py' in another terminal first.")
        sys.exit(1)

    # 1. Collect Name
    name = input("Agent: Hello! I'm your SwitchedOn Assistant. May I have your full name? \nYou: ")
    
    # 2. Collect Phone
    phone = input(f"\nAgent: Thanks {name}. What's your phone number? \nYou: ")
    
    # 3. Collect Service
    service = input("\nAgent: Great. Are you looking for electrical, plumbing, or heating today? \nYou: ")
    service_normalized = "plumbing" if "plum" in service.lower() else ("electrical" if "elec" in service.lower() else "heating")

    # 4. Collect Postcode
    postcode = input("\nAgent: And what's your postcode? \nYou: ")
    
    # 5. Collect Time
    print("\nAgent: I'll check availability for next week.")
    time_pref = input("Agent: Which day and time works best for you? \nYou: ")
    
    # Mock ISO conversion - simplify for demo
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    iso_time = tomorrow.isoformat() + "Z"

    print(f"\n--- Processing Simulation ---")
    print(f"Staging Data: {name} | {phone} | {service_normalized} | {postcode} | {iso_time}")
    
    confirm = input(f"\nAgent: Let me confirm: {name}, {phone}, {service_normalized} at {postcode} for {time_pref}. Correct? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Demo aborted.")
        return

    # Call the actual backend
    payload = {
        "intent": "book",
        "slots": {
            "full_name": name,
            "phone_number": phone,
            "service_type": service_normalized,
            "postcode": postcode,
            "preferred_times": [iso_time]
        },
        "transcript": f"User said: {name}, {phone}, {service}, {postcode}, {time_pref}",
        "confidence": 0.95
    }

    async with httpx.AsyncClient() as client:
        print("\n[Simulator -> /attempt-booking]")
        response = await client.post(f"{BASE_URL}/attempt-booking", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "confirmed":
                print(f"\nAgent: Your booking is CONFIRMED! Reference: {data['booking_reference']}.")
                print(f"Agent: We'll see you on {data['scheduled_time']}.")
            else:
                print(f"\nAgent: I'm sorry, we couldn't book that. Reason: {data.get('reason')}")
        else:
            print(f"\nError: Backend returned {response.status_code}")

    print("\n--- End of Simulation ---")
    print("Check 'calls.json' to see how the backend persisted this interaction.")

if __name__ == "__main__":
    asyncio.run(simulate_booking())
