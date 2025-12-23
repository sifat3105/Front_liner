import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Agent(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agents"  
    )

    name = models.CharField(max_length=100)
    welcome_message = models.TextField(blank=True, default="")
    agent_prompt = models.TextField(help_text="System/instructions for the agent")
    business_details = models.JSONField(default=dict, blank=True)
    voice = models.CharField(max_length=50, default="alloy")
    language = models.CharField(max_length=10, default="bn")
    enabled = models.BooleanField(default=False)

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    theme_primary = models.CharField(max_length=20, default="#16a34a")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "updated_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner_id})"
    


