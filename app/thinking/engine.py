from app.admin.repository import admin_repository
from app.shared.llm.client import llm_client
from app.thinking.models import Intent, ThinkingProfile
from .parser import parse_intent

llm = llm_client


async def think(
    text: str,
    context: list[dict] | None = None,
    profile: ThinkingProfile | None = None,
):
    try:
        tools = await admin_repository.list_tools(enabled_only=True)
    except Exception:
        tools = []

    if not tools:
        return Intent(
            name="conversation",
            action="answer",
            confidence=1.0,
            requires_response=True,
        )

    tool_catalog = "\n".join(
        f'- name="{tool.name}": {tool.description}'
        for tool in tools
    ) or '- conversation: conversa e resposta geral'

    messages = [
        {
            "role": "system",
            "content": f"""
Você é o módulo de interpretação do Jarbas.
Sua função NÃO é responder ao usuário.
Sua função é analisar a mensagem e classificá-la em uma intenção estruturada.
Retorne SOMENTE um JSON válido no seguinte formato:
{{
    "name": "conversation",
    "action": "answer",
    "entities": {{}},
    "confidence": 0.0,
    "requires_response": true
}}
Intenções disponíveis:
{tool_catalog}
Regras:
- Use o name exato de uma tool quando o pedido corresponder à descrição.
- Use conversation para conversa geral ou quando nenhuma tool corresponder.
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
                "content": (
                    "Informações de personalização:\n"
                    f"Vocabulário: {profile.vocabulary}\n"
                    f"Preferências: {profile.preferences}"
                ),
            }
        )
    for entry in (context or [])[-2:]:
        messages.append({"role": "user", "content": entry["user"]})
        messages.append({"role": "assistant", "content": entry["jarbas"]})
    messages.append({"role": "user", "content": text})
    response = await llm.chat(messages)
    result = parse_intent(response)
    print(result)
    return result
