import ollama


async def think(text: str):

    response = ollama.chat(
        model="gemma3:12b",
        messages=[
            {
                "role": "system",
                "content": """
Você é o Thinking do Jarbas.

Sua única função é identificar a intenção do usuário.

Responda SOMENTE JSON e SEMPRE EM PORTUGUES, informalmente e pejorativamente se julgar necessário.

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
        ],
        options={
            "temperature": 1,
        },
    )

    return response["message"]["content"]
