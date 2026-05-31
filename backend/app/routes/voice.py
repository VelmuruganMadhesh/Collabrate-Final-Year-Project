from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.response import api_response
from app.core.security import get_current_user
from app.models.voice import VoiceProcessResponse
from app.services.voice_service import process_voice
from database.mongo import get_database


router = APIRouter(prefix="/voice", tags=["voice"])
logger = get_logger(__name__)


@router.post("/process", response_model=None)
async def voice_process(
    language: str = Form(...),
    transcript: str | None = Form(None),
    audio: UploadFile | None = File(None),
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings()
    db = get_database(settings.mongodb_uri, settings.mongo_db_name)

    if not audio and not transcript:
        logger.warning("Voice process rejected reason=missing_audio_and_transcript")
        raise HTTPException(status_code=400, detail="Provide either audio or transcript.")

    audio_bytes: bytes | None = None
    audio_mime: str | None = None
    if audio:
        audio_bytes = await audio.read()
        audio_mime = audio.content_type

    user_id = str(current_user["_id"])
    logger.info(
        "Voice process requested user_id=%s language=%s has_audio=%s has_transcript=%s audio_mime=%s audio_size=%s",
        user_id,
        language,
        audio_bytes is not None,
        bool(transcript),
        audio_mime,
        len(audio_bytes) if audio_bytes else 0,
    )
    result: VoiceProcessResponse = await process_voice(
        db=db,
        user_id=user_id,
        language=language,
        audio_bytes=audio_bytes,
        audio_mime=audio_mime,
        transcript_text=transcript,
    )
    logger.info(
        "Voice process completed user_id=%s intent=%s transcript_present=%s",
        user_id,
        result.get("detected_intent") if isinstance(result, dict) else None,
        bool(result.get("transcript")) if isinstance(result, dict) else False,
    )
    return api_response(True, data=result, message="Voice processed successfully")

