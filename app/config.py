from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jarbas_name: str
    jarbas_version: str
    environment: str

    class Config:
        env_file = ".env"


settings = Settings()
