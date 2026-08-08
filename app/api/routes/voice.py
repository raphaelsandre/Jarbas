from app.providers.speech.faster_whisper import FasterWhisperProvider
from app.thinking.engine import think
from fastapi import APIRouter, File, UploadFile

speech = FasterWhisperProvider()

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/")
@router.post("")
async def voice(file: UploadFile = File(...)):

    transcript = await speech.transcribe(file)

    thought = await think(transcript)

    return {
        "transcript": transcript,
        "thought": thought,
    }
