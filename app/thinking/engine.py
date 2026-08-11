import httpx
from app.config import settings
from app.thinking.models import ThinkingProfile
from .parser import parse_intent
from app.config import settings

OLLAMA_URL = settings.ollama_url


async def think(
    text: str,
    context: list[dict] | None = None,
    profile: ThinkingProfile | None = None,
):
    messages = [
        {
            "role": "system",
            "content": """
Você é o módulo de interpretação do Jarbas.
Sua função NÃO é responder ao usuário.
Sua função é analisar a mensagem e classificá-la em uma intenção estruturada.
Retorne SOMENTE um JSON válido no seguinte formato:
{
    "name": "conversation",
    "action": "answer",
    "entities": {},
    "confidence": 0.0,
    "requires_response": true
}
Regras:
- "name" identifica o domínio principal da intenção.
- "action" identifica a ação desejada.
- "entities" contém parâmetros relevantes extraídos da mensagem.
- "confidence" deve ser um número entre 0 e 1.
- "requires_response" indica se o sistema deve responder ao usuário.
- Nunca converse com o usuário.
- Nunca explique sua decisão.
- Nunca coloque texto fora do JSON.
""",
        }
    ]
    if profile:
        messages.append(
            {
                "role": "system",
                "content": f"""
                Informações de personalização:
                Vocabulario: ${profile.vocabulary}
                Preferências: ${profile.preferences}
                """,
            }
        )
    for entry in (context or [])[-2:]:
        messages.append(
            {
                "role": "user",
                "content": entry["user"],
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": entry["jarbas"],
            }
        )
    messages.append({"role": "user", "content": text})
    timeout = httpx.Timeout(
        connect=settings.ollama_connect_timeout,
        read=settings.ollama_read_timeout,
        write=settings.ollama_write_timeout,
        pool=settings.ollama_pool_timeout,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.7,
                },
            },
        )
    response.raise_for_status()

    payload = response.json()

    content = payload["message"]["content"]
    for key in (
        "total_duration",
        "load_duration",
        "prompt_eval_duration",
        "eval_duration",
        "prompt_eval_count",
        "eval_count",
    ):
        print(key, payload.get(key))
    data = response.json()

    print("=== OLLAMA RAW ===")
    print(data)

    print("=== THINKING ===")
    print(data.get("message", {}).get("thinking"))

    print("=== CONTENT ===")
    print(data.get("message", {}).get("content"))
    return parse_intent(content)
