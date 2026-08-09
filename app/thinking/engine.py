import httpx
from app.config import settings

OLLAMA_URL = settings.ollama_url


async def think(text: str, context: list[dict] | None = None):
    messages = [
        {
            "role": "system",
            "content": """
Você é o Thinking do Jarbas.
Sua única função é identificar a intenção do usuário.
Responda SOMENTE JSON e SEMPRE EM PORTUGUÊS,
informalmente e pejorativamente se julgar necessário.
Use o histórico recente apenas para entender referências,
continuidade e contexto da mensagem atual.

Exemplo:
{
"intent": "ta querendo abrir o code né"
}
""",
        },
    ]
    for entry in context or []:
        messages.append({
            "role": "user",
            "content": entry["user"],
        })
        messages.append({
            "role": "assistant",
            "content": entry["jarbas"],
        })
    messages.append({
        "role": "user",
        "content": text
    })

    async with httpx.AsyncClient(timeout=100) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "sandre/llama3.1:8b    ",
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 1,
                },
            },
        )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]
