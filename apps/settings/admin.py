from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import AgentPricePerMonth, MinimumTopup, CallCostPerMinute

@admin.register(AgentPricePerMonth)
class AgentPricePerMonthAdmin(UnfoldModelAdmin):
    list_display = ("id", "price")
    ordering = ("-id",)

@admin.register(MinimumTopup)
class MinimumTopupAdmin(UnfoldModelAdmin):
    list_display = ("id", "amount")
    ordering = ("-id",)

@admin.register(CallCostPerMinute)
class CallCostPerMinuteAdmin(UnfoldModelAdmin):
    list_display = ("id", "price")
    ordering = ("-id",)
