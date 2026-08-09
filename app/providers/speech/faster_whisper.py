import tempfile
import os

from app.gateway.models import InputFile
from faster_whisper import WhisperModel

from .base import SpeechProvider


class FasterWhisperProvider(SpeechProvider):
    def __init__(self):
        # tiny, base, small, medium, large-v3...
        self.model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

    async def transcribe(self, file: InputFile) -> str:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:
            tmp.write(file.content)
            path = tmp.name
        try:
            segments, _ = self.model.transcribe(
                path,
                language="pt",
            )
            text = "".join(segment.text for segment in segments)
            return text.strip()
        finally:
            os.remove(path)
