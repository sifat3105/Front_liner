from django.db import IntegrityError, transaction

def create_transcript(assistant_id, type="web"):
    from .models import Transcript
    try:
        with transaction.atomic():
            return Transcript.objects.create(assistant_id=assistant_id, type=type)
    except IntegrityError:
        # created by another process just before us
        return Transcript.objects.get(assistant_id=assistant_id)
    
def get_transcript( transcript_id):
    from .models import Transcript
    return Transcript.objects.get( id=transcript_id)



from channels.db import database_sync_to_async

@database_sync_to_async
def save_transcript_chunks(transcript, user_text, agent_text, assistant_chunk="assistant_chunk", user_chunk="user_chunk", user_audio=None, agent_audio=None):
    from .models import TranscriptChunk
    try:
        chunks = [
            TranscriptChunk(
                transcript=transcript,
                sender="user",
                text=user_text,
                # chunk=user_chunk,
                # audio=user_audio,
            ),
            TranscriptChunk(
                transcript=transcript,
                sender="assistant",
                text=agent_text,
                # chunk=assistant_chunk,
                # audio=agent_audio,
            ),
        ]
        TranscriptChunk.objects.bulk_create(chunks, ignore_conflicts=True)
    except Exception as e:
        print(f"Error saving transcript chunks: {e}")
    return chunks

def get_assistant(public_id):
    from .models import Assistant
    return Assistant.objects.get(public_id=public_id)

def get_history(transcript):
    return list(
            transcript.chunks.order_by("-created_at")[:20].values("sender", "text", "created_at")
        )

def get_assistant_mamory(assistant_id):
    from .models import AssistantMamory
    memory_obj, _ = AssistantMamory.objects.get_or_create(
                assistant_id=assistant_id,
                defaults={ "memory": {}}
            )
    return memory_obj.memory or {}
