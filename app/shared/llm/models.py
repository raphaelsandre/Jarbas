from pydantic import BaseModel, SecretStr


class LLMConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    model: str
