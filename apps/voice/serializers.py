from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Agent
        fields = "__all__"





    

