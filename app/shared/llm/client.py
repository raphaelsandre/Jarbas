from openai import AsyncOpenAI

from .models import LLMConfig
from app.config import settings

config = LLMConfig(
    base_url=settings.ollama_base_url,
    api_key=settings.ollama_api_key,
    model=settings.ollama_model,
)


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key.get_secret_value(),
        )

    @property
    def model(self) -> str:
        return self.config.model

    def set_model(self, model: str) -> None:
        self.config.model = model

    async def list_models(self) -> list[str]:
        try:
            response = await self.client.models.list()
        except Exception:
            return []
        return sorted(item.id for item in response.data)

    async def chat(self, messages: list[dict], *, json_mode: bool = True):
        request = {
            "model": self.config.model,
            "messages": messages,
        }
        if json_mode:
            request["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**request)
        result = response.choices[0].message.content
        print(result)
        return result


llm_client = LLMClient(config)
