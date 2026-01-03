from django.contrib import admin
from .models import CourierList, UserCourier

admin.site.register(CourierList)
admin.site.register(UserCourier)