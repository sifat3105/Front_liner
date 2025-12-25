from celery import shared_task
from django.utils import timezone
from twilio.rest import Client
from datetime import timedelta
from .utils import add_call_cost
from .models import CallLog, Assistant
from django.db import transaction

import os
# Twilio Config
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")

client = Client(account_sid, auth_token)


def twilio_fetch_calls(start_date=None, end_date=None):
    """Fetch call logs from Twilio."""
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
            "from": call._from,
            "to": call.to,
            "duration": call.duration,
            "start_time": call.start_time,
            "end_time": call.end_time,
            "price": call.price,
            "direction": getattr(call, "direction", "").lower(),
            "p": call.price
        })

    return results

from django.http import JsonResponse
def fetch_call_transcriptions(request):
    call_sid = "CA0ec1ac7bc294f19d1f8e045a8a5fcfa3"
    
    transcriptions = client.transcriptions(call_sid)
    print(f"transcriptions: {transcriptions}")
    return JsonResponse({"transcriptions": "Transcriptions fetched. Check console for details."})


@shared_task
def sync_twilio_call_logs():
    """
    Every 5 minutes:
    - Update existing CallLog entries
    - Create new entries if not found
    - Fix duplicates automatically
    """

    end_date = timezone.now()
    start_date = end_date - timedelta(minutes=10)

    twilio_calls = twilio_fetch_calls(start_date, end_date)

    for data in twilio_calls:
        call_sid = data.get("sid")
        if not call_sid:
            continue

        record_sid = data.get("record_sid")

        # Convert timestamp to string (Twilio gives datetime)
        timestamp = data.get("start_time")
        if timestamp:
            timestamp = str(timestamp)

        log = (
            CallLog.objects
            .filter(call_sid=call_sid)
            .select_related(
                "assistant",
                "assistant__owner",
                "assistant__owner__profile",
            )
            .first()
        )
        if not log:
            continue
        if log.call_status == "completed":
            continue
        
        log.record_sid = record_sid
        log.call_status = data["status"]
        log.call_duration = data["duration"]
        log.caller = data["from"]
        log.callee = data["to"]
        log.timestamp = timestamp
        log.direction = data.get("direction", "").lower()
        log.recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Recordings/{record_sid}.mp3"
        log.save()
        
        print(f"log: {log}")
        # -------- Cost Calculation -------- #
        profile = log.assistant.owner.profile
        if data["status"] == "completed":
            cost = add_call_cost(data["duration"], profile)
            log.cost = cost
            log.save()
        else:
            log.cost = data["p"]
            log.save()

    return "Twilio call logs synced."