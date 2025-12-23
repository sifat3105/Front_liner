from twilio.rest import Client
from datetime import datetime, timedelta
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def fetch_all_calls(start_date=None, end_date=None):
    """
    Fetch all call logs from Twilio.
    Optional start_date and end_date (datetime objects)
    """
    filters = {}
    if start_date:
        filters["start_time_after"] = start_date
    if end_date:
        filters["start_time_before"] = end_date

    calls = client.calls.list(**filters)
    

    results = []
    for call in calls:
        recordings = call.recordings.list()
        results.append({
            "sid": call.sid,
            "record_sid": recordings[0].sid if recordings else None,
            "status": call.status,
            "from": call.from_formatted,
            "to": call.to,
            "duration": call.duration,
            "start_time": call.start_time,
            "end_time": call.end_time,
            "price": call.price,
        })

    return results


def fetch_call_recordings(call_sid):
    recordings = client.recordings.list(call_sid=call_sid)
    print(recordings)
    urls = [r.uri.replace(".json", "") for r in recordings]
    return urls
