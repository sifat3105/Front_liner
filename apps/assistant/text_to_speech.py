import asyncio
import re
from django.http import StreamingHttpResponse
from edge_tts import Communicate


def generate_tts_stream(text: str, voice: str = "bn-BD-NabanitaNeural") -> StreamingHttpResponse:
    """
    Generate a streaming HTTP response with real-time Bangla TTS audio.
    """
    if not text:
        return StreamingHttpResponse("No text provided", status=400)

    # Split the input text into sentences
    sentences = re.split(r'(?<=[。！？!?.])', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    def audio_stream_generator():
        async def stream_sentence(sentence):
            communicate = Communicate(text=sentence, voice=voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            for sentence in sentences:
                async_gen = stream_sentence(sentence)

                agen = async_gen.aiter()
                while True:
                    try:
                        chunk = loop.run_until_complete(agen.anext())
                        yield chunk
                    except StopAsyncIteration:
                        break
        finally:
            loop.close()

    return StreamingHttpResponse(audio_stream_generator(), content_type="audio/mpeg")
