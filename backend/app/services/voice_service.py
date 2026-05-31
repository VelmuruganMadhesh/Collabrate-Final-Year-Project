from ai_module.voice_processor import process_voice_request

from app.core.logging import get_logger


logger = get_logger(__name__)


async def process_voice(
    *,
    db,
    user_id: str,
    language: str,
    audio_bytes: bytes | None,
    audio_mime: str | None,
    transcript_text: str | None,
):
    logger.info(
        "Voice service started user_id=%s language=%s has_audio=%s has_transcript=%s",
        user_id,
        language,
        audio_bytes is not None,
        bool(transcript_text),
    )
    result = await process_voice_request(
        db=db,
        user_id=user_id,
        language=language,
        audio_bytes=audio_bytes,
        audio_mime=audio_mime,
        transcript_text=transcript_text,
    )
    logger.info(
        "Voice service finished user_id=%s intent=%s",
        user_id,
        result.get("detected_intent") if isinstance(result, dict) else None,
    )
    return result

