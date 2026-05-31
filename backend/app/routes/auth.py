from fastapi import APIRouter, Depends, HTTPException, status

from app.core.response import api_response
from app.core.security import get_current_user
from app.models.user import UserCreateRequest, UserLoginRequest
from app.services.auth_service import authenticate_user
from app.services.user_service import create_user, to_user_public
from app.core.config import get_settings
from app.core.logging import get_logger, mask_email
from database.mongo import get_database


router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register")
async def register(payload: UserCreateRequest):
    settings = get_settings()
    db = get_database(settings.mongodb_uri, settings.mongo_db_name)
    safe_email = mask_email(payload.email)
    logger.info("Registration requested email=%s", safe_email)

    try:
        user_public = await create_user(
            db=db,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            password=payload.password,
            language=payload.language,
        )
    except ValueError as e:
        logger.warning("Registration validation failed email=%s detail=%s", safe_email, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    logger.info("Registration completed user_id=%s email=%s", user_public.get("_id"), safe_email)
    return api_response(True, data=user_public, message="Registration successful")


@router.post("/login")
async def login(payload: UserLoginRequest):
    safe_email = mask_email(payload.email)
    logger.info("Login requested email=%s", safe_email)
    token, user_public = await authenticate_user(email=payload.email, password=payload.password)
    logger.info("Login completed user_id=%s email=%s", user_public.get("_id"), safe_email)
    return api_response(True, data={"token": token, "user": user_public}, message="Login successful")


@router.get("/profile")
async def profile(current_user: dict = Depends(get_current_user)):
    logger.info("Profile requested user_id=%s", str(current_user.get("_id")))
    return api_response(True, data=to_user_public(current_user), message="Profile fetched successfully")

