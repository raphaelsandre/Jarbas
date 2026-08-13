from app.providers import speech
from uuid import uuid4
from app.observer.hermes.hermes import observer
from app.context.short_term import add_context
from app.response.responder import respond
from app.thinking.engine import think
from app.observer.hermes.reader import get_hermes_profile
from app.context.short_term import get_context
from fastapi import Request, HTTPException
from app.handle.orchestrator import create_orchestrator
from datetime import datetime
from app.gateway.models import GatewayInput, GatewayResult
from app.gateway.parser import parse_input


def mark(label: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {label}")


orchestrator = create_orchestrator()


async def process_gateway_request(
    request: Request,
) -> GatewayResult:
    gateway_input = await parse_input(request)
    return await process_gateway_input(gateway_input)


async def process_gateway_input(gateway_input: GatewayInput) -> GatewayResult:
    """
    Process the input received from the gateway and return the result.
    """
    print(gateway_input)
    if gateway_input.text is not None:
        text = gateway_input.text
    elif gateway_input.files:
        text = await speech.transcribe(gateway_input.files[0])
    else:
        raise HTTPException(
            status_code=400, detail="Nenhuma entrada pode ser utilizada"
        )
    context = await get_context()
    await observer(request_id=uuid4().hex, text=text)
    profile = get_hermes_profile()
    mark("THINK START")
    intent = await think(text=text, context=context, profile=profile)
    mark("THINK DONE")
    result = await orchestrator.execute(intent)
    mark("ORCHESTRATOR DONE")
    output = await respond(
        user_input=text, intent=intent, result=result, context=context, profile=profile
    )
    mark("RESPONDER DONE")
    if output is not None:
        await add_context(user_input=text, jarbas_output=output)
        mark("CONTEXT DONE")
    mark("AE CARLALHO")
    print("Output: ", output)
    return GatewayResult(input=text, output=output, intent=intent)
