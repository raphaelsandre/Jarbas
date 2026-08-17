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
    piesocket_enabled: bool = False
    piesocket_ws_url: str = (
        "wss://ws.core.sandre.dev/v3/chatroom"
        "?api_key=jarbas-devel&notify_self=1"
    )
    jarbas_tool_allowed_origins: str = ""
    pwa_dist_dir: str = "/opt/Assistant/JarbasPwa/dist"

    class Config:
        env_file = ".env"


settings = Settings()
