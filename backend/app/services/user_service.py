from typing import Optional

from fastapi import HTTPException, status
from bson import ObjectId

from app.core.logging import get_logger, mask_email
from app.core.security import hash_password, validate_password_rules
from database.mongo import get_database


logger = get_logger(__name__)


async def create_user(
    *,
    db,
    name: str,
    email: str,
    phone: Optional[str],
    password: str,
    language: Optional[str],
) -> dict:
    validate_password_rules(password)
    users_col = db["users"]
    safe_email = mask_email(email)

    existing = await users_col.find_one({"email": email})
    if existing:
        logger.warning("Create user rejected reason=email_exists email=%s", safe_email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    doc = {
        "name": name,
        "email": email,
        "phone": phone,
        "password_hash": hash_password(password),
        "language": language,
    }
    result = await users_col.insert_one(doc)
    user_id_str = str(result.inserted_id)
    doc["_id"] = user_id_str
    logger.info("User document created user_id=%s email=%s", user_id_str, safe_email)

    # Create a default account record for the new user (demo-friendly).
    accounts_col = db["accounts"]
    account_number = str(ObjectId())[-10:]  # simple pseudo account number
    await accounts_col.insert_one(
        {
            "user_id": user_id_str,
            "account_number": account_number,
            "currency": "INR",
            "balance": 10000.0,
            "created_at": None,
        }
    )
    logger.info("Default account created user_id=%s account_number=%s", user_id_str, account_number)

    # Remove sensitive fields
    doc.pop("password_hash", None)
    return doc


async def get_user_by_email(db, email: str) -> Optional[dict]:
    users_col = db["users"]
    user = await users_col.find_one({"email": email})
    logger.debug("User lookup by email email=%s found=%s", mask_email(email), bool(user))
    return user


def to_user_public(user_doc: dict) -> dict:
    # Convert Mongo doc -> response doc, stripping sensitive fields.
    public = {
        "_id": str(user_doc.get("_id")),
        "name": user_doc.get("name"),
        "email": user_doc.get("email"),
        "phone": user_doc.get("phone"),
        "language": user_doc.get("language"),
    }
    return public

