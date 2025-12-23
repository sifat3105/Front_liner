import asyncio
import json
import os
import aiohttp
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .utils import get_assistant, create_transcript, get_transcript, get_history, get_assistant_mamory, save_transcript_chunks
from . models import Transcript
from .assistant_workflow import compile_dynamic_agent

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REALTIME_MODEL = "gpt-4o-realtime-preview"
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY")

class AssistantConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.public_id = self.scope['url_route']['kwargs']['public_id']
        self.assistant = await database_sync_to_async(get_assistant)(self.public_id)
        self.workflow = await database_sync_to_async(compile_dynamic_agent)(self.assistant)

        session_key = self.scope["cookies"].get("careon_session_id")

        if session_key:
            try:
                self.transcript = await database_sync_to_async(get_transcript)(session_key)
            except Transcript.DoesNotExist:
                self.transcript = await database_sync_to_async(create_transcript)(self.assistant.id, "web")
        else:
            self.transcript = await database_sync_to_async(create_transcript)(self.assistant.id, "web")
        self.room_group_name = f"room_id_{self.transcript.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send(json.dumps({"transcript_session_id": self.transcript.id}))
        print("connected")
        print(f"this is session id:{session_key}")
        
    async def disconnect(self, code):
            pass

    async def receive(self, text_data=None, bytes_data=None):
        
        try:
            data = json.loads(text_data)
            user_message = data.get("text", "")
            if data.get("type") == "user_audio_chunk":
                user_audio_chunk = data.get("data")
                print(f"user audio chunk received", user_audio_chunk)
                user_audio_chunk_index = data.get("chunk_index")
                user_audio_chunk_timestamp = data.get("timestamp")
                print(f"user audio chunk {user_audio_chunk_index} received")
                

            voice = "bn-BD-NabanitaNeural"
            history = await database_sync_to_async(get_history)(self.transcript)
            memory = await database_sync_to_async(get_assistant_mamory)(self.assistant.id)
            result = self.workflow.invoke({
                "input_text": user_message,
                "history": history,
                "memory": memory or {},
                "session_id": self.transcript.id
                })
            text = result["answer"]
            if result.get('call_support_api'):
                await self.send(json.dumps({"call_support_api": result['call_support_api']}))
            await self.send(json.dumps({"text": text}))
            
            if not text:
                await self.send(json.dumps({"error": "No text provided"}))
                return
            await self.stream_audio(text, user_message)

        except Exception as e:
            await self.send(json.dumps({"error": str(e)}))
            
    async def stream_audio(self, text, user_message):
        voice_id = str(self.assistant.voice).strip().replace('"', '').replace("'", "")
        # if not voice_id:
        # voice_id = "pNInz6obpgDQGcFmaJgB"  # Rachel

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



