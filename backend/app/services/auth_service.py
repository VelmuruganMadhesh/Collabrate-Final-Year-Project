from fastapi import HTTPException, status

from app.core.security import create_access_token, verify_password
from app.core.config import get_settings
from app.core.logging import get_logger, mask_email
from database.mongo import get_database


logger = get_logger(__name__)


async def authenticate_user(*, email: str, password: str) -> tuple[str, dict]:
    settings = get_settings()
    db = get_database(settings.mongodb_uri, settings.mongo_db_name)
    users_col = db["users"]
    safe_email = mask_email(email)

    user = await users_col.find_one({"email": email})
    if not user:
        logger.warning("Authentication failed reason=user_not_found email=%s", safe_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not verify_password(password, user.get("password_hash", "")):
        logger.warning("Authentication failed reason=invalid_password email=%s", safe_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    user_id = str(user["_id"])
    token = create_access_token(subject=user_id, settings=settings)
    user_public = {
        "_id": user_id,
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "language": user.get("language"),
    }
    logger.info("Authentication succeeded user_id=%s email=%s", user_id, safe_email)
    return token, user_public

