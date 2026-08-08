import time
import ollama

prompt = """
    Você é o mecanismo de intenções do Jarbas.

Responda apenas JSON válido.

Nunca explique.

Nunca converse.

Nunca use markdown.

Intenções disponíveis:

- open_code
- open_chat
- restart_container
- shutdown_server

Frase:

"Jarbas, vamos codar."
"""

inicio = time.perf_counter()

response = ollama.chat(
    model="gemma3:12b",
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

fim = time.perf_counter()

print(response["message"]["content"])
print(f"{fim - inicio:.2f}s")
