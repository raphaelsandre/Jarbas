import json
from .models import Intent


def parse_intent(content: str) -> Intent:
    data = json.loads(content)
    return Intent(
        name=data.get("name", "Unknown"),
        action=data.get("action"),
        entities=data.get("entities", {}),
        confidence=data.get("confidence", 0.0),
        requires_response=data.get("requires_response", True),
    )
