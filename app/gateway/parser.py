from fastapi import Request
from starlette.datastructures import UploadFile

from .models import GatewayInput, InputFile


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
        data = {}

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
