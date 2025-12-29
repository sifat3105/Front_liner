from rest_framework import serializers
from .models import Courierlist

class CourierCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Courierlist
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']
