from abc import ABC, abstractmethod
from fastapi import UploadFile


class SpeechProvider(ABC):
    @abstractmethod
    async def transcribe(self, file: UploadFile) -> str:
        pass
