from typing import Dict, List, Optional
from .base import DukeApiServiceBase
from datetime import datetime
import os
import dotenv

dotenv.load_dotenv()

class EventsApiService(DukeApiServiceBase):
    def __init__(self, api_base_url, api_key: Optional[str] = None):
        super().__init__(api_base_url, api_key)
        # Load relevant metadata
    
    def get_future_events(self, future_days) -> List[Dict]:
        # pass in custom params for this specific route
        params = {
            'future_days': future_days,
            'feed_type': 'simple'
        }
        
        api_response = self._make_request("", params=params)

        if not api_response or "events" not in api_response:
            return []

        extracted_events = []

        for event in api_response.get("events"):
            try:
                # Parse and format timestamps
                start_ts = event.get("start_timestamp", "")
                end_ts = event.get("end_timestamp", "")

                formatted_start = None
                formatted_end = None

                if start_ts:
                    start_dt = datetime.strptime(start_ts, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_start = start_dt.strftime("%b %d, %Y %I:%M %p")

                if end_ts:
                    end_dt = datetime.strptime(end_ts, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_end = end_dt.strftime("%b %d, %Y %I:%M %p")

                # Extract fields with fallbacks
                extracted_event = {
                    "summary": event.get("summary", "No Title").strip(),
                    "description": event.get("description", "").strip(),
                    "start_time": formatted_start,
                    "end_time": formatted_end,
                    "sponsor": event.get("sponsor"),
                    "co_sponsors": event.get("co_sponsors"),
                    "location": event.get("location", {}).get("address", "TBD"),
                    "event_url": event.get("event_url", ""),
                }

                extracted_events.append(extracted_event)

            except Exception as e:
                # Log or handle unexpected formatting errors per event
                print(f"Error processing event: {e}")
                continue

        return extracted_events

        
def main():
    duke_api_service = EventsApiService(os.getenv('DUKE_API_EVENTS_BASE_URI'), os.getenv('DUKE_API_KEY'))
    events = duke_api_service.get_future_events(1)
    print(events)

if __name__=='__main__':
    main()