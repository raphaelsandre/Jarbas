import httpx

from app.config import settings


OLLAMA_URL = settings.ollama_url
OLLAMA_MODEL = settings.ollama_model


async def generate_answer(
    user_input: str,
    context: list[dict] | None = None,
    profile=None,
) -> str:
    messages: list[dict] = [
        {
            "role": "system",
            "content": (
                "Você é Jarbas, um assistente pessoal. "
                "Responda ao usuário de forma natural, útil e direta. "
                "Não classifique intenções. "
                "Não retorne JSON. "
                "Retorne somente a resposta destinada ao usuário."
            ),
        }
    ]

    if profile is not None:
        messages.append(
            {
                "role": "system",
                "content": f"Perfil do usuário:\n{profile}",
            }
        )

    if context:
        messages.extend(context)

    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    timeout = httpx.Timeout(
        connect=5.0,
        read=180.0,
        write=10.0,
        pool=5.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.7,
                },
            },
        )

        if response.is_error:
            print("=== OLLAMA RESPONSE ERROR ===")
            print("status:", response.status_code)
            print("body:", response.text)
            print("headers:", dict(response.headers))

        response.raise_for_status()

    payload = response.json()

    return payload["message"]["content"]
