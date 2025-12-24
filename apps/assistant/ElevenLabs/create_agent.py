from elevenlabs.client import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

def create_agent(
    name: str,
    voice_id: str,
    first_message: str,
    language: str,
    system_prompt: str,
    tools: list,
    file_data: list = None
):
    return client.conversational_ai.agents.create(
        name=name,
        conversation_config={
            "agent": {
                "voice_id": voice_id,
                "first_message": first_message,
                "prompt": {
                    "prompt": system_prompt,
                    "tools": [],
                    "attachments": file_data
                }
            }
        }
    )
    

