from rest_framework import serializers
from .models import CourierList
class CourierCompanySerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = CourierList
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']
        
    def get_is_active(self, obj):
        user_couriers = self.context.get('user_couriers', [])
        for uc in user_couriers:
            if uc.courier_id == obj.id:
                return uc.is_active
        return False
