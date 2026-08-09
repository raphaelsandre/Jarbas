import asyncio
import json
import os
from dataclasses import asdict, dataclass

from datetime import datetime, timezone
from pathlib import Path

HERMES_INPUT = Path("/var/lib/jarbas/hermes/input.jsonl")


@dataclass(frozen=True)
class HermesObservation:
    request_id: str
    text: str
    created_at: str


def _append(observation: HermesObservation) -> None:
    HERMES_INPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    line = (
        json.dumps(
            asdict(observation),
            ensure_ascii=False,
        )
        + "\n"
    )
    fd = os.open(
        HERMES_INPUT,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o640,
    )
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


async def observe(request_id: str, text: str) -> None:
    obsevation = HermesObservation(
        request_id=request_id,
        text=text,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    (await asyncio.to_thread(_append, observation=obsevation),)
