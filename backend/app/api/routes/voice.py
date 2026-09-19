from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from backend.app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice Engine"])


class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"
    voice_id: Optional[str] = None


@router.post("/transcribe", summary="Transcribe speech audio into query text")
async def transcribe_voice(
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    language: str = Form("en"),
):
    upload = file or audio
    audio_bytes = await upload.read() if upload else None
    filename = upload.filename if upload and upload.filename else "audio.webm"
    content_type = upload.content_type if upload and upload.content_type else "audio/webm"
    return await voice_service.transcribe(
        audio_bytes=audio_bytes,
        language=language,
        filename=filename,
        content_type=content_type,
    )


@router.post("/synthesize", summary="Synthesize response text to speech audio via Fish Audio")
async def synthesize_voice(req: SynthesizeRequest):
    return await voice_service.synthesize(
        text=req.text,
        language=req.language,
        voice_id=req.voice_id,
    )
