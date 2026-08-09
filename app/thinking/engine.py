import httpx
from app.config import settings
OLLAMA_URL = settings.ollama_url


async def think(text: str):
    messages = [
        {
            "role": "system",
            "content": """
Você é o Thinking do Jarbas.
Sua única função é identificar a intenção do usuário.
Responda SOMENTE JSON e SEMPRE EM PORTUGUÊS,
informalmente e pejorativamente se julgar necessário.

Exemplo:
{
    "intent": "abrir code"
}
""",
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    async with httpx.AsyncClient(timeout=100) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "gemma3:12b",
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 1,
                },
            },
        )

    response.raise_for_status()

    data = response.json()

    print(data)

    return data["message"]["content"]