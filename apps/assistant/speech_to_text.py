import asyncio
import base64
import json
import numpy as np
import sounddevice as sd
import websockets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024


async def _transcribe(self):
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-transcribe"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    transcribed_text = ""

    async with websockets.connect(url, extra_headers=headers) as ws:
        def callback(indata, frames, time, status):
            if status:
                print(status)
            pcm16 = (indata * 32767).astype(np.int16)
            audio_b64 = base64.b64encode(pcm16.tobytes()).decode("utf-8")
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64})),
                asyncio.get_event_loop()
            )

        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback)
        with stream:
            await ws.send(json.dumps({"type": "response.create"}))

            async for msg in ws:
                data = json.loads(msg)
                if data.get("type") == "response.output_text.delta":
                    transcribed_text += data["delta"]
                    print(data["delta"], end="", flush=True)

                elif data.get("type") == "response.completed":
                    break

    return transcribed_text

