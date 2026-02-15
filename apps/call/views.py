from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from apps.assistant.models import Assistant
from django.shortcuts import get_object_or_404
from .models import CallLog, CallCampaign
from .serializers import CallLogSerializer
from twilio.rest import Client
from . utils import synthesize_speech_memory
from apps.phone_number.models import PhoneNumber
import os,io,csv

class StartCallView(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"error": "Phone number is required"}, status=400)
        

        client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))

        call = client.calls.create(
            to=phone,
            from_=os.getenv("TWILIO_NUMBER"),
            url=os.getenv("CALL_WEBHOOK_URL") or os.getenv("TWILIO_VOICE_WEBHOOK_URL"),
            record=True
        )
        try:
            assistant = Assistant.objects.get(twilio_number=os.getenv("TWILIO_NUMBER"))
            CallLog.objects.create(
                assistant=assistant,
                call_sid=call.sid,
                call_status="ringing",
                direction="outbound",
                caller=os.getenv("TWILIO_NUMBER"),
                callee=phone,
            )
        except:
            pass
        return Response({"status": "calling", "call_sid": call.sid})
    
class CallCampaignAPIView(APIView):

    def post(self, request):
        is_single = request.data.get("is_single")
        if is_single:
            is_single = True
        else:
            is_single = False
        assistant_id = request.data.get("assistant_id")
        assistant = Assistant.objects.get(id=assistant_id)
        text = assistant.first_message
        
        # Twilio client
        client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))

        # ---------- SINGLE CALL LOGIC ----------
        if is_single:
            name = request.data.get("name")
            number_id = request.data.get("number_id")
            to_number = request.data.get("to_phone")
            
            if "<NAME>" in text:
                text = text.replace("<NAME>", name)
            return self.process_single_call(
                request, client, text, number_id, to_number
            )

        # ---------- CSV BULK PROCESSING ----------
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"error": "CSV file is required"}, status=400)

        try:
            data = csv_file.read().decode("utf-8")
        except:
            return Response({"error": "Invalid CSV encoding"}, status=400)

        io_string = io.StringIO(data)
        reader = csv.DictReader(io_string)

        total_calls = 0
        failed = 0

        number_id = request.data.get("number_id")
        fron_obj = PhoneNumber.objects.get(id=number_id)
        from_number = fron_obj.phone_number

        base_url = f"{request.scheme}://{request.get_host()}"
        base_url = "https://cornelia-preindulgent-leigh.ngrok-free.dev"

        for row in reader:
            print(row)

            name = row.get("name") or row.get("Name")
            to_number = row.get("number") or row.get("phone") or row.get("phone_number")
            designation = row.get("designation") or row.get("job") 
            company = row.get("company")
            business_type = row.get("business type") or row.get("business_type") or row.get("type")

            if not to_number:
                failed += 1
                continue

            try:
                if "<NAME>" in text:
                    text = text.replace("<NAME>", name)
                file_path, audio_id = synthesize_speech_memory(text, to_number)

                call = client.calls.create(
                    to=to_number,
                    from_=from_number,
                    url=f"{base_url}/voice?id={audio_id}",
                    record=True
                )

                try:
                    print(f"Assistant found: {assistant}, calling {to_number}, from {from_number}, text: {text}")
                    CallLog.objects.create(
                        assistant=assistant,
                        call_sid=call.sid,
                        call_status="ringing",
                        direction="outbound",
                        caller=from_number,
                        callee=to_number,
                    )
                    CallCampaign.objects.create(
                        phone_number=to_number,
                        name=name,
                        designation=designation,
                        company=company,
                        business_type=business_type,
                    )
                except Exception as e:
                    print(e)
                    pass

                total_calls += 1

            except Exception as e:
                failed += 1

        return Response({
            "status": "bulk_complete",
            "success_calls": total_calls,
            "failed": failed
        })

    # -----------------------------------------------------------
    # HANDLE SINGLE CALL
    # -----------------------------------------------------------
    def process_single_call(self, request, client, text, number_id, to_number):

        designation = request.data.get("designation")
        company = request.data.get("company")
        business_type = request.data.get("business_type")

        file_path, audio_id = synthesize_speech_memory(text, to_number)

        fron_obj = PhoneNumber.objects.get(id=number_id)
        from_number = fron_obj.phone_number

        # base_url = f"{request.scheme}://{request.get_host()}"
        base_url = "https://cornelia-preindulgent-leigh.ngrok-free.dev"

        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=f"{base_url}/voice?id={audio_id}",
            record=True
        )

        try:
            assistant = Assistant.objects.get(id=request.data.get("assistant_id"))
            CallLog.objects.create(
                assistant=assistant,
                call_sid=call.sid,
                call_status="ringing",
                direction="outbound",
                caller=from_number,
                callee=to_number,
            )
            CallCampaign.objects.create(
                phone_number=to_number,
                name=request.data.get("name"),
                designation=designation,
                company=company,
                business_type=business_type,
            )
        except Exception as e:
            print(e)
            pass

        return Response({
            "status": "single_success",
            "file_path": file_path,
            "audio_id": audio_id
        })



class CallLogStatsAPIView(APIView):
    """
    Returns call logs grouped by assistant and call status
    """
    def get(self, request):
        # Optional date filters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        qs = CallLog.objects.all()

        if start_date:
            qs = qs.filter(timestamp__gte=start_date)
        if end_date:
            qs = qs.filter(timestamp__lte=end_date)

        # Group by assistant
        assistants_data = []
        assistants = qs.values("assistant__id", "assistant__name").distinct()

        for a in assistants:
            assistant_id = a["assistant__id"]
            assistant_name = a["assistant__name"]
            assistant_calls = qs.filter(assistant_id=assistant_id)

            data = {
                "assistant_id": assistant_id,
                "assistant_name": assistant_name,
                "total_calls": assistant_calls.count(),
                "completed": assistant_calls.filter(call_status="completed").count(),
                "failed": assistant_calls.filter(call_status="failed").count(),
                "ringing": assistant_calls.filter(call_status="ringing").count(),
            }
            assistants_data.append(data)

        return Response({"data": assistants_data})
    

class CallLogListAPIView(APIView):

    def get(self, request):
        protocol = request.META.get('HTTP_X_FORWARDED_PROTO', 'http')
        base_url = f"{protocol}://{request.META['HTTP_HOST']}"
        call_logs = CallLog.objects.filter(assistant__owner=request.user).order_by("-created_at")
        serializer = CallLogSerializer(call_logs, many=True).data
        data=[]
        for call_log in serializer:
            call_log["recording_url"] = f"{base_url}/api/play/{call_log['record_sid']}/"
            data.append(call_log)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Call logs fetched successfully.",
            "data": data
            }, status=status.HTTP_200_OK)
    
class CallLogDetailSingleAPIView(APIView):
    """
    Returns details of a single call log by its ID
    """

    def get(self, request, pk):
        call_log = get_object_or_404(CallLog, pk=pk)
        data = CallLogSerializer(call_log).data
        protocol = request.META.get('HTTP_X_FORWARDED_PROTO', 'http')
        base_url = f"{protocol}://{request.META['HTTP_HOST']}"
        data["recording_url"] = f"{base_url}/api/play/{call_log.record_sid}/"
        return Response(data, status=status.HTTP_200_OK)
    

from .services.twilio_service import fetch_all_calls, fetch_call_recordings
from datetime import datetime, timedelta

class TwilioCallLogsAPIView(APIView):
    """
    Fetch all call logs from Twilio API
    """

    def get(self, request):
        # Optional query params
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        calls = fetch_all_calls(start_dt, end_dt)
        return Response({"data": calls})


class TwillioRecordingsAPIView(APIView):
    
    def get(self, request, call_sid):
        recordings = fetch_call_recordings(call_sid)
        return Response({"data": recordings})
    
    
    
import requests
from django.http import HttpResponse
from django.conf import settings
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH")

def play_recording(request, recording_sid):

    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"

    response = requests.get(
        twilio_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        stream=True
    )

    if response.status_code != 200:
        return HttpResponse("Unable to fetch recording", status=400)

    return HttpResponse(
        response.content,
        content_type="audio/mpeg"
    )

