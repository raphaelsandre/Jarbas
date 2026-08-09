from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jarbas_name: str
    jarbas_version: str
    environment: str
    ollama_url: str
    jarbas_api_key: str
    jarbas_user_agent: str

    class Config:
        env_file = ".env"


settings = Settings()
