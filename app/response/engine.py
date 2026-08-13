from app.shared.llm.client import llm_client

llm = llm_client


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

    for interaction in context[-2:]:
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

    response = await llm.chat(messages)

    return response
