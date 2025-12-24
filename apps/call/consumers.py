
import json
import tempfile
from channels.generic.websocket import AsyncWebsocketConsumer
import base64
import aiohttp
from openai import OpenAI
from apps.assistant.utils import get_assistant, get_assistant_mamory, get_history, save_transcript_chunks
from apps.assistant.assistant_workflow import compile_dynamic_agent
from channels.db import database_sync_to_async
from .utils import create_call_transcript
import os

ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

class TwilioStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract identifiers from query params
        params = self.scope["query_string"].decode()
        query = dict(q.split('=') for q in params.split('&'))
        self.public_key = query.get("public_key")
        self.assistant_id = query.get("assistant_id")
        self.caller = query.get("caller")
        self.assistant = await database_sync_to_async(get_assistant)(self.public_key)
        self.workflow = await database_sync_to_async(compile_dynamic_agent)(self.assistant)
        self.transcript = await database_sync_to_async(create_call_transcript)(self.assistant.id, "call")

        await self.accept()
        print(f"✅ Connected Twilio stream for caller {self.caller} | "
              f"user {self.public_key} | agent {self.assistant_id}")

        # Init buffers
        self.audio_buffer = bytearray()
        self.last_text = ""

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        if data.get("event") == "media":
            chunk = base64.b64decode(data["media"]["payload"])
            self.audio_buffer.extend(chunk)
            await self.transcribe_audio(bytes(chunk))

        elif data.get("event") == "start":
            print("📞 Call started")
        elif data.get("event") == "stop":
            print("🛑 Call stopped")

    async def assistant_reply(self, text):
        print("🤖 Generating assistant reply...")
 

        history = await database_sync_to_async(get_history)(self.transcript)
        memory = await database_sync_to_async(get_assistant_mamory)(self.assistant.id)
        try:
            result = self.workflow.invoke({
                "input_text": text,
                "history": history,
                "memory": memory or {},
                "session_id": self.transcript.id
                })
            ai_reply = result["answer"]
        except Exception as e:
            ai_reply = "Sorry, I had an issue processing that."
            print("Assistant error:", e)

        print(f"🤖 Reply: {ai_reply}")

        await self.stream_audio(ai_reply, text)

   
    async def transcribe_audio(self, audio_bytes):
        print("Transcribing audio...")
        """
        Transcribe audio to text using ElevenLabs Speech-to-Text API.
        """
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": ELEVEN_API_KEY}

        # Save incoming audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Send to ElevenLabs via async aiohttp
        async with aiohttp.ClientSession() as session:
            with open(tmp_path, "rb") as f:
                form_data = aiohttp.FormData()
                form_data.add_field("file", f, filename="audio.wav", content_type="audio/wav")

                form_data.add_field("model_id", "scribe_v2")

                async with session.post(url, headers=headers, data=form_data) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        await self.send(json.dumps({
                            "type": "error",
                            "message": f"STT failed: {error_text}"
                        }))
                        return

                    result = await resp.json()
                    text = result.get("text", "")
                    await self.assistant_reply(text)
                    # Send back transcription to WebSocket client
                    await self.send(json.dumps({
                        "type": "transcription",
                        "text": text,
                        "language": result.get("language", "unknown"),
                        "duration": result.get("duration", None)
                    }))
    async def stream_audio(self, text, user_message):
        print("Streaming audio...")
        voice_id = str(self.assistant.voice).strip().replace('"', '').replace("'", "")
        # if not voice_id:
        voice_id = "pNInz6obpgDQGcFmaJgB"  # Rachel

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    await self.send(json.dumps({"type": "error", "message": error}))
                    return

                full_audio = b""
                async for chunk in resp.content.iter_chunked(1024):
                    full_audio += chunk
                    
                await self.send(json.dumps({
                    "type": "audio_chunk",
                    "data": full_audio.decode("latin1")
                }))
                
                await self.send(json.dumps({"type": "end"}))
                await save_transcript_chunks(
                self.transcript,
                user_message,
                text,
                full_audio.decode("latin1")
            )
                
