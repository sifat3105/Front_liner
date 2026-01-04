from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import CustomerInfo

@admin.register(CustomerInfo)
class CustomerInfoAdmin(UnfoldModelAdmin):
    list_display = ("id", "owner", "location", "contact", "platform", "price", "status")
    list_filter = ("status", "platform")
    search_fields = ("owner__username", "location", "contact")
    readonly_fields = ()
    ordering = ("-id",)
