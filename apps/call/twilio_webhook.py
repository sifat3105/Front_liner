import logging
import os

from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from twilio.twiml.voice_response import VoiceResponse

from apps.assistant.models import Assistant
from .models import CallLog

logger = logging.getLogger(__name__)


class TwilioVoiceWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return self._build_twiml(request)

    def post(self, request):
        return self._build_twiml(request)

    def _build_twiml(self, request):
        call_sid = request.data.get("CallSid") or request.GET.get("CallSid")
        from_number = request.data.get("From") or request.GET.get("From")
        to_number = request.data.get("To") or request.GET.get("To")

        assistant = self._resolve_assistant(call_sid=call_sid, to_number=to_number)
        if not assistant:
            logger.warning("No call assistant matched for call_sid=%s to=%s", call_sid, to_number)
            response = VoiceResponse()
            response.say("No assistant is configured for this number.")
            response.hangup()
            return HttpResponse(str(response), content_type="text/xml")

        self._upsert_call_log(
            assistant=assistant,
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
        )

        stream_url = self._build_stream_url(request)

        response = VoiceResponse()
        connect = response.connect()
        stream = connect.stream(url=stream_url)
        stream.parameter(name="assistant_id", value=str(assistant.id))
        stream.parameter(name="assistant_public_id", value=str(assistant.public_id))
        if call_sid:
            stream.parameter(name="call_sid", value=call_sid)
        if to_number:
            stream.parameter(name="to", value=to_number)

        return HttpResponse(str(response), content_type="text/xml")

    @staticmethod
    def _resolve_assistant(call_sid=None, to_number=None):
        assistant = None

        if call_sid:
            call_log = CallLog.objects.select_related("assistant").filter(call_sid=call_sid).first()
            if call_log and call_log.assistant_id:
                assistant = call_log.assistant

        if not assistant and to_number:
            assistant = (
                Assistant.objects
                .filter(agent_type="call", twilio_number=to_number, enabled=True)
                .order_by("-updated_at")
                .first()
            )

        if not assistant and to_number:
            assistant = (
                Assistant.objects
                .filter(agent_type="call", twilio_number=to_number)
                .order_by("-updated_at")
                .first()
            )

        return assistant

    @staticmethod
    def _upsert_call_log(assistant, call_sid, from_number, to_number):
        if not call_sid:
            return

        call_log, created = CallLog.objects.get_or_create(
            call_sid=call_sid,
            defaults={
                "assistant": assistant,
                "call_status": "ringing",
                "direction": "inbound" if assistant.twilio_number == to_number else "outbound",
                "caller": from_number,
                "callee": to_number,
            },
        )

        if not created:
            changed = False
            if not call_log.assistant_id:
                call_log.assistant = assistant
                changed = True
            if from_number and call_log.caller != from_number:
                call_log.caller = from_number
                changed = True
            if to_number and call_log.callee != to_number:
                call_log.callee = to_number
                changed = True
            if changed:
                call_log.save(update_fields=["assistant", "caller", "callee", "updated_at"])

    @staticmethod
    def _build_stream_url(request):
        explicit_url = os.getenv("TWILIO_STREAM_WS_URL", "").strip()
        if explicit_url:
            return explicit_url

        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        secure = forwarded_proto == "https" or request.is_secure()
        scheme = "wss" if secure else "ws"

        return f"{scheme}://{request.get_host()}/ws/twilio/stream/"
