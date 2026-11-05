# core/llm_client.py
import asyncio
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI
from core.config import settings

T = TypeVar("T", bound=BaseModel)

class AIClient:
    def __init__(self):
        # Initialize standard async client
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.model_name
        self.temperature = settings.temperature

    async def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        """
        Forces the LLM to return data matching the provided Pydantic model.
        """
        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=response_model,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            # In a production 2026 system, this would route to Datadog/Sentry
            print(f"LLM Generation Error: {e}")
            raise

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes raw audio bytes using OpenAI's Whisper API.
        """
        # OpenAI's API requires a file-like object with a name attribute.
        # We wrap the bytes in a tuple to satisfy this requirement without saving to disk.
        audio_file = (filename, audio_bytes, "audio/wav")
        
        try:
            # We use the synchronous client in a thread to avoid blocking, 
            # or the async client if using the latest SDK.
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt="The audio is a highly technical software engineering interview response about system architecture, latency, and Go/Next.js." # Gives Whisper context for technical jargon
            )
            return response.text
        except Exception as e:
            print(f"Whisper Transcription Error: {e}")
            return "Error transcribing audio."    

# Instantiate a global async client to avoid recreating TCP connections
llm = AIClient()