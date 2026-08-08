class SpeechService:
    def __init__(self, provider):
        self.provider = provider

    async def transcribe(self, file):
        return await self.provider.transcribe(file)
