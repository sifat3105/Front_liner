from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Account, Subscription

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'role', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_superuser')}),
        ('Referral', {'fields': ('refer_user', 'parent')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Account)
admin.site.register(Subscription)
