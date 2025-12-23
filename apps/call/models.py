from django.db import models
from apps.assistant.models import Assistant

class CallLog(models.Model):
    assistant = models.ForeignKey(
        Assistant,
        on_delete=models.CASCADE,
        related_name="call_logs",
        null=True,
        blank=True,
    )
    call_sid = models.CharField(max_length=255)
    record_sid = models.CharField(max_length=255, blank=True, null=True)
    call_status = models.CharField(max_length=50)
    call_duration = models.CharField(max_length=50, blank=True, null=True)
    direction = models.CharField(max_length=50, blank=True, null=True)
    caller = models.CharField(max_length=50, blank=True, null=True)
    callee = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.CharField(max_length=100, blank=True, null=True)
    recording_url = models.URLField(blank=True, null=True)
    
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.00, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "call_calllog"
        indexes = [
            models.Index(fields=["assistant", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.call_status} | {self.call_sid}"
    

class CallCampaign(models.Model):
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=50, blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True)


    def save(self, *args, **kwargs):
        # First save to get an ID if it's a new object
        creating = self.pk is None  
        super().save(*args, **kwargs)

        # Now serial_number can be created
        if creating and not self.serial_number:
            serial = 1000 + self.pk
            self.serial_number = f"HSBS{serial}"

            # Save again only to update serial_number
            super().save(update_fields=["serial_number"])

    



    
