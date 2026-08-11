from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jarbas_name: str
    jarbas_version: str
    environment: str
    ollama_url: str
    jarbas_api_key: str
    jarbas_user_agent: str
    ollama_model: str
    ollama_keep_alive: str
    ollama_connect_timeout: float
    ollama_read_timeout: float
    ollama_write_timeout: float
    ollama_pool_timeout: float

    class Config:
        env_file = ".env"


settings = Settings()
