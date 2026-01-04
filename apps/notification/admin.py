from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Notification  # import the model, don't redefine it

@admin.register(Notification)
class NotificationAdmin(UnfoldModelAdmin):
    list_display = ("title", "user", "read", "created_at", "updated_at")
    list_filter = ("read", "created_at")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
