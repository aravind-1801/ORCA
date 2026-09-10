from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from backend.app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice Engine"])


class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("/transcribe", summary="Transcribe speech audio into query text")
async def transcribe_voice(
    audio: Optional[UploadFile] = File(None),
    language: str = Form("en"),
):
    audio_bytes = await audio.read() if audio else None
    return await voice_service.transcribe(audio_bytes, language)


@router.post("/synthesize", summary="Synthesize response text to speech instructions")
async def synthesize_voice(req: SynthesizeRequest):
    return await voice_service.synthesize(req.text, req.language)
