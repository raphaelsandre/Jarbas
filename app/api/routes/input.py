from dataclasses import dataclass
from typing import Any
from fastapi import Request, APIRouter, HTTPException, Depends
from starlette.datastructures import UploadFile
from app.context.short_term import add_context, get_context
from app.providers.speech.faster_whisper import FasterWhisperProvider
from app.thinking.engine import think
from app.security.auth import authenticate_request


speech = FasterWhisperProvider()

router = APIRouter(
    prefix="/input",
    tags=["gateway"],
    dependencies=[
        Depends(authenticate_request),
    ],
)


@dataclass
class InputFile:
    filename: str
    content_type: str
    content: bytes


@dataclass
class GatewayInput:
    text: str | None = None
    data: dict[str, Any] | None = None
    files: list[InputFile] | None = None


async def parse_input(request: Request) -> GatewayInput:
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()

    if content_type == "text/plain":
        return GatewayInput(text=(await request.body()).decode("utf-8"))

    if content_type == "application/json":
        body = await request.json()

        return GatewayInput(
            text=body.get("text"),
            data=body,
        )

    if content_type == "multipart/form-data":
        form = await request.form()

        files: list[InputFile] = []
        data: dict[str, Any] = {}

        for key, value in form.multi_items():
            if isinstance(value, UploadFile):
                files.append(
                    InputFile(
                        filename=value.filename or "",
                        content_type=value.content_type or "",
                        content=await value.read(),
                    )
                )

            else:
                data[key] = value

        return GatewayInput(
            text=data.get("text"),
            data=data or None,
            files=files or None,
        )

    raise ValueError(f"Unsupported content type: {content_type}")


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
    thought = await think(
        text=text,
        context=context,
    )
    await add_context(
        user_input=text,
        jarbas_output=thought
    )
    return {
        "input": text,
        "thought": thought,
    }
