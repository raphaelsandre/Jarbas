from fastapi import Request, HTTPException, APIRouter, Depends
from app.gateway.parser import parse_input
from app.context.short_term import add_context, get_context
from app.providers.speech.faster_whisper import FasterWhisperProvider
from app.thinking.engine import think
from app.security.auth import authenticate_request
from app.observer.hermes.hermes import observer
from uuid import uuid4
from app.observer.hermes.reader import get_hermes_profile
from app.handle.orchestrator import create_orchestrator
from app.response.responder import respond
from datetime import datetime


def mark(label: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {label}")


speech = FasterWhisperProvider()
orchestrator = create_orchestrator()
router = APIRouter(
    prefix="/input",
    tags=["gateway"],
    dependencies=[
        Depends(authenticate_request),
    ],
)


@router.post("")
async def input_gateway(request: Request):
    parsed = await parse_input(request)
    if parsed.text is not None:
        text = parsed.text
    elif parsed.files:
        text = await speech.transcribe(parsed.files[0])
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
    print("DESCONECTOU", await request.is_disconnected())
    mark("AE CARLALHO")
    print("Output: ", output)
    return {"input": text, "intent": intent, "orchestrator": result, "output": output}
