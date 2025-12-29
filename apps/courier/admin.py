from django.contrib import admin
from .models import Courierlist, UserCourier

# Register your models here.

# =====================
# Courierlist Admin
# =====================
@admin.register(Courierlist)
class CourierlistAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


# =====================
# UserCourier Admin
# =====================
@admin.register(UserCourier)
class UserCourierAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('courier_list',)  # nice UI for ManyToMany
    search_fields = ('user__username',)
