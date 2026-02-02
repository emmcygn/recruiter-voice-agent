import httpx
import os
import logging

logger = logging.getLogger(__name__)

class CalClient:
    def __init__(self):
        self.api_key = os.environ.get("CAL_API_KEY")
        self.event_type_id = os.environ.get("CAL_EVENT_TYPE_ID") # The ID of the SwitchedOn service on Cal
        self.base_url = "https://api.cal.com/v2"

    async def create_booking(self, full_name: str, email: str, start_time: str, phone: str):
        if not self.api_key:
            return None

        async with httpx.AsyncClient() as client:
            # Note: Cal.com v2 /bookings endpoint
            response = await client.post(
                f"{self.base_url}/bookings",
                headers={"Authorization": f"Bearer {self.api_key}", "cal-api-version": "2024-06-11"},
                json={
                    "start": start_time,
                    "eventTypeId": int(self.event_type_id),
                    "attendee": {
                        "name": full_name,
                        "email": email, # Fallback to a placeholder if not provided
                        "timeZone": "Europe/London"
                    },
                    "metadata": {"phone": phone}
                }
            )

            if response.status_code == 201:
                return response.json().get("data", {}).get("uid")
            else:
                logger.error(f"Cal.com booking failed: {response.text}")
                return None
