from django.contrib import admin
from .models import CustomerInfo

# Register your models here.

@admin.register(CustomerInfo)
class CustomerInfoAdmin(admin.ModelAdmin):

    list_display = (
        'id', 
        'owner', 
        'location', 
        'contact', 
        'price', 
        'platform', 
        'status'
    )
    list_filter = ('status', 'platform', 'owner')
    search_fields = ('location', 'contact', 'owner__username')
    ordering = ('-id',)  # shows latest entries first
    readonly_fields = ('id',)

    # Optional: auto-fill owner with the logged-in user when creating
    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
