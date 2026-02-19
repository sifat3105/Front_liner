import asyncio
import base64
import json
import logging
import os
import audioop
import contextlib
import wave
from io import BytesIO
from urllib.parse import parse_qs

import aiohttp
import azure.cognitiveservices.speech as speechsdk
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.assistant.assistant_workflow import compile_dynamic_agent
from apps.assistant.models import Assistant
from apps.assistant.utils import (
    get_assistant_mamory,
    get_history,
    save_transcript_chunks,
)
from apps.call.models import CallLog
from .utils import create_call_transcript

logger = logging.getLogger(__name__)

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
DEEPGRAM_MODEL = os.environ.get("DEEPGRAM_MODEL", "nova-3")
DEEPGRAM_LANGUAGE = os.environ.get("DEEPGRAM_LANGUAGE", "").strip()

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "")
AZURE_TTS_DEFAULT_VOICE = os.environ.get("AZURE_TTS_DEFAULT_VOICE", "en-US-JennyNeural")


class TwilioStreamConsumer(AsyncWebsocketConsumer):
    """
    Handles bidirectional Twilio media stream:
    - inbound media payload (mulaw/8khz) -> buffered ASR
    - ASR text -> LLM workflow
    - LLM reply -> TTS (mulaw/8khz) -> Twilio media outbound

    Expected websocket route: /ws/twilio/stream/
    """

    async def connect(self):
        self.query_params = {
            key: values[0]
            for key, values in parse_qs(self.scope.get("query_string", b"").decode()).items()
            if values
        }

        self.stream_sid = None
        self.call_sid = self.query_params.get("call_sid")
        self.assistant = None
        self.workflow = None
        self.transcript = None

        self.audio_buffer = bytearray()
        self.min_buffer_bytes = 12000  # ~1.5 sec at 8k mulaw
        self.processing_task = None
        self.last_text = ""

        await self.accept()
        logger.info("Twilio stream websocket connected")

    async def disconnect(self, close_code):
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.processing_task

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON on Twilio stream")
            return

        event = data.get("event")
        if event == "start":
            await self._handle_start(data.get("start", {}))
            return

        if event == "media":
            await self._handle_media(data.get("media", {}))
            return

        if event == "stop":
            logger.info("Twilio stream stopped for call_sid=%s", self.call_sid)
            return

    async def _handle_start(self, start_payload):
        self.stream_sid = start_payload.get("streamSid") or self.stream_sid
        self.call_sid = start_payload.get("callSid") or self.call_sid

        custom_params = start_payload.get("customParameters") or {}
        to_number = custom_params.get("to") or start_payload.get("to")

        assistant_id = (
            custom_params.get("assistant_id")
            or self.query_params.get("assistant_id")
        )
        assistant_public_id = (
            custom_params.get("assistant_public_id")
            or self.query_params.get("assistant_public_id")
            or self.query_params.get("public_key")
        )

        self.assistant = await self._resolve_assistant(
            call_sid=self.call_sid,
            assistant_id=assistant_id,
            assistant_public_id=assistant_public_id,
            to_number=to_number,
        )

        if not self.assistant:
            logger.error("No assistant resolved for call_sid=%s", self.call_sid)
            await self.close(code=4004)
            return

        self.workflow = await database_sync_to_async(compile_dynamic_agent)(self.assistant)
        self.transcript = await database_sync_to_async(create_call_transcript)(self.assistant.id, "call")

        await self._backfill_calllog_assistant(self.call_sid, self.assistant.id)

        logger.info(
            "Twilio stream started: call_sid=%s stream_sid=%s assistant_id=%s",
            self.call_sid,
            self.stream_sid,
            self.assistant.id,
        )

    async def _handle_media(self, media_payload):
        payload_b64 = media_payload.get("payload")
        if not payload_b64:
            return

        if not self.assistant or not self.transcript:
            return

        try:
            mulaw_chunk = base64.b64decode(payload_b64)
        except Exception:
            logger.warning("Failed to decode media payload for call_sid=%s", self.call_sid)
            return

        self.audio_buffer.extend(mulaw_chunk)

        if len(self.audio_buffer) < self.min_buffer_bytes:
            return

        if self.processing_task and not self.processing_task.done():
            return

        buffered = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        self.processing_task = asyncio.create_task(self._process_audio_turn(buffered))

    async def _process_audio_turn(self, mulaw_audio: bytes):
        text = await self._transcribe_mulaw_audio(mulaw_audio)
        if not text:
            return

        text = text.strip()
        if not text or text == self.last_text:
            return

        self.last_text = text
        await self._handle_llm_and_reply(text)

    async def _handle_llm_and_reply(self, user_text: str):
        history = await database_sync_to_async(get_history)(self.transcript)
        memory = await database_sync_to_async(get_assistant_mamory)(self.assistant.id)

        try:
            result = await database_sync_to_async(self.workflow.invoke)(
                {
                    "input_text": user_text,
                    "history": history,
                    "memory": memory or {},
                    "session_id": self.transcript.id,
                }
            )
            ai_reply = (result or {}).get("answer", "")
        except Exception:
            logger.exception("LLM workflow failed for call_sid=%s", self.call_sid)
            ai_reply = "Sorry, I had an issue processing that."

        if not ai_reply:
            return

        await self._stream_tts_to_twilio(ai_reply)
        await save_transcript_chunks(
            self.transcript,
            user_text,
            ai_reply,
            "",
        )

    async def _transcribe_mulaw_audio(self, mulaw_audio: bytes) -> str:
        if not DEEPGRAM_API_KEY:
            logger.error("DEEPGRAM_API_KEY missing")
            return ""

        pcm_8k = audioop.ulaw2lin(mulaw_audio, 2)
        pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 16000, None)

        wav_bytes = self._pcm_to_wav_bytes(pcm_16k, sample_rate=16000)

        assistant_language = str(getattr(self.assistant, "language", "") or "").strip()
        deepgram_language = DEEPGRAM_LANGUAGE or assistant_language
        if deepgram_language and "-" in deepgram_language:
            deepgram_language = deepgram_language.split("-")[0]

        url = (
            "https://api.deepgram.com/v1/listen"
            f"?model={DEEPGRAM_MODEL}"
            "&smart_format=true&punctuate=true"
        )
        if deepgram_language:
            url += f"&language={deepgram_language}"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=wav_bytes) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        "Deepgram STT failed call_sid=%s status=%s body=%s",
                        self.call_sid,
                        resp.status,
                        body,
                    )
                    return ""

                result = await resp.json()
                channels = (
                    result.get("results", {})
                    .get("channels", [])
                )
                if not channels:
                    return ""
                alternatives = channels[0].get("alternatives", [])
                if not alternatives:
                    return ""
                return (alternatives[0].get("transcript") or "").strip()

    async def _stream_tts_to_twilio(self, text: str):
        if not self.stream_sid:
            return

        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            logger.error("AZURE_SPEECH_KEY or AZURE_SPEECH_REGION missing")
            return

        preferred_voice = str(getattr(self.assistant, "voice", "") or "").strip().replace('"', "").replace("'", "")
        voices = [preferred_voice, AZURE_TTS_DEFAULT_VOICE]
        seen = set()
        ordered_voices = []
        for voice in voices:
            if voice and voice not in seen:
                seen.add(voice)
                ordered_voices.append(voice)

        ulaw_audio = b""
        for voice_name in ordered_voices:
            ulaw_audio = await asyncio.to_thread(self._synthesize_azure_mulaw, text, voice_name)
            if ulaw_audio:
                break

        if not ulaw_audio:
            logger.warning("Azure TTS produced no audio for call_sid=%s", self.call_sid)
            return

        for chunk in self._chunk_bytes(ulaw_audio, 320):
            await self.send(
                text_data=json.dumps(
                    {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": base64.b64encode(chunk).decode("ascii"),
                        },
                    }
                )
            )
            await asyncio.sleep(0.04)

        await self.send(
            text_data=json.dumps(
                {
                    "event": "mark",
                    "streamSid": self.stream_sid,
                    "mark": {"name": "assistant_response_end"},
                }
            )
        )

    @staticmethod
    def _synthesize_azure_mulaw(text: str, voice_name: str) -> bytes:
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY,
                region=AZURE_SPEECH_REGION,
            )
            speech_config.speech_synthesis_voice_name = voice_name
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw
            )

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None,
            )

            result = synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return bytes(result.audio_data or b"")

            cancellation_details = speechsdk.CancellationDetails.from_result(result)
            logger.warning(
                "Azure TTS canceled: reason=%s error=%s voice=%s",
                cancellation_details.reason,
                cancellation_details.error_details,
                voice_name,
            )
            return b""
        except Exception:
            logger.exception("Azure TTS exception for voice=%s", voice_name)
            return b""

    @staticmethod
    def _chunk_bytes(data: bytes, size: int):
        for i in range(0, len(data), size):
            yield data[i:i + size]

    @staticmethod
    def _pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int) -> bytes:
        bio = BytesIO()
        with wave.open(bio, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        return bio.getvalue()

    @database_sync_to_async
    def _resolve_assistant(self, call_sid=None, assistant_id=None, assistant_public_id=None, to_number=None):
        assistant = None

        if assistant_id:
            assistant = Assistant.objects.filter(id=assistant_id, agent_type="call").first()

        if not assistant and assistant_public_id:
            assistant = Assistant.objects.filter(public_id=assistant_public_id, agent_type="call").first()

        if not assistant and call_sid:
            call_log = CallLog.objects.select_related("assistant").filter(call_sid=call_sid).first()
            if call_log and call_log.assistant_id:
                assistant = call_log.assistant

        if not assistant and to_number:
            assistant = (
                Assistant.objects
                .filter(agent_type="call", twilio_number=to_number, enabled=True)
                .order_by("-updated_at")
                .first()
            )

        if not assistant and to_number:
            assistant = (
                Assistant.objects
                .filter(agent_type="call", twilio_number=to_number)
                .order_by("-updated_at")
                .first()
            )

        return assistant

    @database_sync_to_async
    def _backfill_calllog_assistant(self, call_sid, assistant_id):
        if not call_sid or not assistant_id:
            return
        call_log = CallLog.objects.filter(call_sid=call_sid).first()
        if call_log and not call_log.assistant_id:
            call_log.assistant_id = assistant_id
            call_log.save(update_fields=["assistant", "updated_at"])






import websockets
BACKEND_WS_URL = "ws://127.0.0.1:8001/ws"


class BridgeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("[BRIDGE] NGS connected")

        self.backend = None
        self.t1 = None
        self.t2 = None
        self._q = asyncio.Queue()

        try:
            self.backend = await websockets.connect(
                BACKEND_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                max_size=None,
            )
            print("[BRIDGE] connected to backend:", BACKEND_WS_URL)

            self.t1 = asyncio.create_task(self.relay_ngs_to_backend())
            self.t2 = asyncio.create_task(self.relay_backend_to_ngs())

        except Exception as e:
            print("[BRIDGE] error on connect:", repr(e))
            await self.close()

    async def disconnect(self, close_code):
        print("[BRIDGE] disconnect:", close_code)

        for t in (self.t1, self.t2):
            if t:
                t.cancel()

        if self.backend is not None:
            try:
                await self.backend.close()
            except Exception:
                pass

        print("[BRIDGE] closed")

    async def websocket_receive(self, message):
        # Push incoming frames into a queue, so relay task can consume them
        if "text" in message:
            await self._q.put(("text", message["text"]))
        elif "bytes" in message:
            await self._q.put(("bytes", message["bytes"]))

    async def relay_ngs_to_backend(self):
        """NGS -> backend"""
        try:
            while True:
                kind, payload = await self._q.get()
                if kind == "text":
                    await self.backend.send(payload)
                else:
                    await self.backend.send(payload)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[BRIDGE] relay_ngs_to_backend error:", repr(e))
            await self.close()

    async def relay_backend_to_ngs(self):
        """backend -> NGS"""
        try:
            while True:
                data = await self.backend.recv()
                if isinstance(data, str):
                    await self.send(text_data=data)
                else:
                    await self.send(bytes_data=data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[BRIDGE] relay_backend_to_ngs error:", repr(e))
            await self.close()