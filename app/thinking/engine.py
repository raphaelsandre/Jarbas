from app.thinking.models import ThinkingProfile
from .parser import parse_intent
from app.shared.llm.client import llm_client
llm = llm_client

async def think(
    text: str,
    context: list[dict] | None = None,
    profile: ThinkingProfile | None = None
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
    response = await llm.chat(messages)
    result = parse_intent(response)
    print(result)
    return result

