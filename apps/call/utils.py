from django.db import IntegrityError, transaction
from apps.assistant.models import Transcript
from apps.phone_number.models import PhoneNumber
from apps.settings.models import CallCostPerMinute
from apps.assistant.models import Assistant
from decimal import Decimal
from apps.transaction.utils import create_transaction
from io import BytesIO
import wave
import azure.cognitiveservices.speech as speechsdk
import os
import uuid

def create_call_transcript(assistant_id, type="call"):
    try:
        with transaction.atomic():
            return Transcript.objects.create(assistant_id=assistant_id, type=type)
    except IntegrityError:
        # created by another process just before us
        return Transcript.objects.get(assistant_id=assistant_id)
    
    


def add_call_cost(duration, profile):

    call_cost = CallCostPerMinute.objects.first()
    
    print(f"profile: {profile}")

    per_sec_cost = call_cost.price / Decimal("60")
    total_cost = per_sec_cost * Decimal(duration)
    print(f"total_cost: {total_cost}")

    with transaction.atomic():
        profile.total_cost += total_cost
        profile.total_duration += int(duration)
        profile.balance -= total_cost
        profile.total_calls += 1
        profile.save()
        create_transaction(
                user = profile.user,
                status = "completed",
                category = "call",
                amount = total_cost,
                description = "Call cost charged successfully.",
                purpose = "Call Charge",
                payment_method = "balance"
            )
        print(f"profile.total_cost: {profile.total_cost}")
        
        return total_cost
    



AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


AUDIO_FOLDER = "audio_files"

os.makedirs(AUDIO_FOLDER, exist_ok=True)

def synthesize_speech_memory(text,unique_id, voice_id="bn-BD-PradeepNeural"):
    if unique_id is None:
        unique_id = str(uuid.uuid4())
    if "+" in unique_id:
        unique_id = unique_id.replace("+", "P")
    raw_file = os.path.join(AUDIO_FOLDER, f"audio_raw_{unique_id}.raw")
    wav_file_path = os.path.join(AUDIO_FOLDER, f"audio_{unique_id}.wav")
    raw_file_path = os.path.join(AUDIO_FOLDER, f"audio_raw_{unique_id}.raw")

    for file_path in [wav_file_path, raw_file_path]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print("Deleted existing file:", file_path)

    # Azure TTS config (same as before)
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice_id
    audio_config = speechsdk.audio.AudioOutputConfig(filename=raw_file)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config, audio_config)

    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        return None, None

    # Convert to WAV
    with open(raw_file, "rb") as f:
        pcm_data = f.read()

    with wave.open(wav_file_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_data)

    return wav_file_path, unique_id