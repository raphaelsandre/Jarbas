from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jarbas_name: str
    jarbas_version: str
    environment: str
    jarbas_api_key: str
    jarbas_user_agent: str
    ollama_model: str
    ollama_api_key: str
    ollama_base_url: str

    class Config:
        env_file = ".env"


settings = Settings()
