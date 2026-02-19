from django.urls import path
from . import views
from .tasks import fetch_call_transcriptions
from .twilio_webhook import TwilioVoiceWebhookAPIView

urlpatterns = [
    path("twilio/start_call/", views.StartCallView.as_view(), name="start_call"),
    path("twilio/voice/", TwilioVoiceWebhookAPIView.as_view(), name="twilio_voice_webhook"),
    path("call_campaign/", views.CallCampaignAPIView.as_view(), name="call_campaign"),

    path("call-logs/stats/", views.CallLogStatsAPIView.as_view(), name="call_logs_stats"),
    path("call-logs/",  views.CallLogListAPIView.as_view(), name="call_logs_list"),
    path("call-logs/<int:pk>/",  views.CallLogDetailSingleAPIView.as_view(), name="call_log_detail"),

    path("twilio/calls/", views.TwilioCallLogsAPIView.as_view(), name="twilio_calls"),
    path("twilio/recordings/<str:call_sid>/", views.TwillioRecordingsAPIView.as_view(), name="twilio_recordings"),  
    
    path("play/<str:recording_sid>/", views.play_recording),

    
    path("test/", fetch_call_transcriptions ),
    
    # NGS API Routes 
    path("ngs/<int:order_id>/voice.xml", views.NGSVoiceXMLView.as_view(), name="ngs_voice_xml"),
    path("webhooks/ngs/status", views.NGSStatusCallbackView.as_view(), name="ngs_status_callback"),
    
]
