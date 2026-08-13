from openai import AsyncOpenAI

from .models import LLMConfig
from app.config import settings

config = LLMConfig(
    base_url = settings.ollama_base_url,
    api_key= settings.ollama_api_key,
    model= settings.ollama_model,
)

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url= config.base_url,
            api_key= config.api_key.get_secret_value(),
        )

    async def chat(self, messages: list[dict]):
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            response_format={
                "type": "json_object"
            }
        )
        result = response.choices[0].message.content
        print(result)
        return result
llm_client = LLMClient(config)