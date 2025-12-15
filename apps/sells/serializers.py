from rest_framework import serializers
from .models import CustomerInfo


class CustomerInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomerInfo model.
    Converts CustomerInfo instances to JSON and validates input data.
    """
    class Meta:
        model = CustomerInfo
        # Explicitly listing fields is more professional than using '__all__'
        fields = [
            'id',
            'owner',
            'location',
            'contact',
            'price',
            'platform',
            'status',
        ]
        # read_only_fields = ['id']  # ID should not be editable
