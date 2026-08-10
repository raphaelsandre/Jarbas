import json
from pathlib import Path
from app.thinking.models import ThinkingProfile

PROFILE_PATH = Path(
    "/var/lib/jarbas/hermes/profile.json"
)

def get_hermes_profile() -> ThinkingProfile | None:
    if not PROFILE_PATH.exists():
        return None
    
    data = json.loads(
        PROFILE_PATH.read_text(
            encoding="utf-8"
       ) 
    )
    return ThinkingProfile.model_validate(data)
