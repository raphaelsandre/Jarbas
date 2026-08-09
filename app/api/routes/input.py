from fastapi import Request, HTTPException, APIRouter, Depends
from app.gateway.parser import parse_input
from app.context.short_term import add_context, get_context
from app.providers.speech.faster_whisper import FasterWhisperProvider
from app.thinking.engine import think
from app.security.auth import authenticate_request
from app.observer.hermes import observe
from uuid import uuid4

speech = FasterWhisperProvider()

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
    await observe(
        request_id=uuid4().hex,
        text=text
    )
    thought = await think(
        text=text,
        context=context,
    )
    await add_context(user_input=text, jarbas_output=thought)
    return {
        "input": text,
        "thought": thought,
    }
