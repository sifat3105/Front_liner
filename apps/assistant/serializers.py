from asyncio.log import logger
from rest_framework import serializers
from django.db import transaction
from apps import assistant
from .models import Assistant, AssistantFile
from django.urls import reverse
from .ElevenLabs.create_agent import create_agent


class AssistantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assistant
        fields = [
            "id", "name", "first_message_mode", "first_message", "system_prompt", "voice",
            "language", "enabled", "model", "max_tokens", "temperature", "public_id", "theme_primary",
            "crisis_keywords", "crisis_keywords_prompt", "description", "avatar_url", "config",
            'created_at', 'updated_at'
        ]
        read_only_fields = ("owner",)




    def create(self, validated_data):
        owner = self.context["request"].user
        files = validated_data.pop("files", None)


        obj = Assistant.objects.create(
            owner=owner,
            **validated_data,
        )

        # Save uploaded files
        if files:
            for f in files:
                AssistantFile.objects.create(assistant=obj, file=f)

            # Build embed HTML
            # request = self.context.get("request")
            # if request:
            #     script_url = request.build_absolute_uri(reverse("embed_js"))
            #     obj.embed_html = f"""
            #         <careon-ai-widget
            #             assistant-id="{obj.public_id}"
            #             public-key="{obj.public_id}">
            #         </careon-ai-widget>
            #         <script src="{script_url}" async type="text/javascript"></script>
            #     """

            obj.save()

            # Prepare file context for ElevenLabs
            file_context = []
            for f in obj.files.all():
                try:
                    content = f.file.read().decode("utf-8")
                    file_context.append({
                        "name": f.file.name,
                        "content": content
                    })
                except Exception as e:
                    logger.warning(f"Could not read file {f.file.name}: {e}")

            # Create ElevenLabs agent
            # agent =create_agent(
            #     name=obj.name,
            #     voice_id=obj.voice,
            #     first_message=obj.first_message,
            #     language=obj.language,
            #     system_prompt=obj.system_prompt,
            #     tools= [obj.config] if isinstance(obj.config, dict) else obj.config,
            #     file_data=file_context
            # )
            # obj.eleven_agent_id = agent.agent_id
            obj.save()

        return obj


    
    def update(self, instance, validated_data):
        files = validated_data.pop("files", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if files is not None:
            instance.files.all().delete()
            for f in files:
                AssistantFile.objects.create(assistant=instance, file=f)

        return instance
    
class AssistantWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = ['id', 'name', 'public_id', 'embed_html']
    

class AssistantListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assistant
        fields = ["id", "name", "language", "enabled", "created_at", "updated_at"]


from rest_framework import serializers
from .models import Transcript, TranscriptChunk


class TranscriptChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptChunk
        fields = [
            "id", "sender", "text", "chunk", "audio", "created_at", "updated_at",
        ]

import base64
class TranscriptSerializer(serializers.ModelSerializer):
    chunks = TranscriptChunkSerializer(many=True, read_only=True)
    audio_chunks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transcript
        fields = [ 
            "id", "call_id", "assistant", "ended_reason", "type", "successs_evalation", 
            "score", "start_time", "end_time", "cost", "duration", "chunks", "audio_chunks",
        ]
        read_only_fields = ["duration", "call_id"]

    def create(self, validated_data):
        """Auto-generate call_id if missing."""
        import uuid
        if not validated_data.get("call_id"):
            validated_data["call_id"] = str(uuid.uuid4())
        return super().create(validated_data)
    
    def get_audio_chunks(self, obj):
        chunks = []
        for a in obj.chunks.all():
            chunk = a.chunk
            if isinstance(chunk, str):
                chunk = chunk.encode('latin1')
            chunks.append(chunk)
        audio_data = b"".join(chunks)
        return base64.b64encode(audio_data).decode('utf-8')

class TranscriptListSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Transcript
        fields = [
            "id",
            "call_id",
            "assistant",
            "type",
            'duration',
            "start_time",
            "end_time",
            "cost",
            "score",
        ]

    def get_duration(self, obj):
        return obj.duration



    

