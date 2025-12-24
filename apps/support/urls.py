from django.urls import path
from .views import SupportTicketCreateView, CallSupportTicketCreateView

urlpatterns = [
    path("support-tickets/", SupportTicketCreateView.as_view(), name="support-ticket-create"),
    path("call-support-tickets/", CallSupportTicketCreateView.as_view(), name="call-support-ticket-create"),
]
