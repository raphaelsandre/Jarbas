from app.orchestrator.models import ExecutionResult
from app.thinking.models import Intent
import httpx
from .engine import generate_answer


async def respond(
    *,
    user_input: str,
    intent: Intent,
    result: ExecutionResult,
    context: list[dict] | None = None,
    profile=None,
) -> str | None:
    if not intent.requires_response:
        return None

    if result.response_hint == "generate_answer":
        try:
            return await generate_answer(
                user_input=user_input,
                context=context,
                profile=profile,
            )
        except httpx.HTTPStatusError as exc:
            print("RESPONDER HTTP ERROR:", exc)
            return None

    if result.response_hint == "tool_response":
        response = result.data.get("response") or result.data.get("message")
        if response is not None:
            return str(response)
        return "A tool foi executada com sucesso."

    if result.response_hint == "unsupported_intent":
        return "Ainda não sei como lidar com esse pedido."

    if result.response_hint == "execution_error":
        return "Ocorreu um erro enquanto eu tentava executar isso."

    return None
