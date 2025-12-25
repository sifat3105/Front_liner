from django.db import models
from django.contrib.auth import get_user_model
from apps.assistant.models import Assistant
User = get_user_model()

class SupportTicket(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_tickets")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    issue_description = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )

    def __str__(self):
        return f"{self.name} - {self.status}"
    
    
class CallSupportTicket(models.Model):
    CT_STATUS = [
        ("panding", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]
    subject = models.CharField(max_length=100, blank=True, null=True)
    queries = models.TextField(blank=True, null=True)
    issue_description = models.TextField()
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    preferred_time = models.DateTimeField(blank=True, null=True)
    agent = models.ForeignKey(Assistant, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_call_tickets")
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, choices=CT_STATUS, default="panding" )
    
    
