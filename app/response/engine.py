from app.shared.llm.client import llm_client

llm = llm_client


async def generate_answer(
    user_input: str,
    context: list[dict] | None = None,
    profile=None,
) -> str:
    system_content = (
        "Você é Jarbas, um assistente pessoal. "
        "Responda ao usuário de forma natural. "
        "Não classifique intenções. "
        "Não retorne JSON. "
        "Retorne somente a resposta."
    )

    if profile is not None:
        system_content += f"\n\nPerfil do usuário:\n{profile}"

    messages: list[dict] = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

    for interaction in (context or [])[-2:]:
        if interaction.get("user"):
            messages.append(
                {
                    "role": "user",
                    "content": interaction["user"],
                }
            )

        if interaction.get("jarbas"):
            messages.append(
                {
                    "role": "assistant",
                    "content": interaction["jarbas"],
                }
            )

    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    response = await llm.chat(messages, json_mode=False)

    return response
