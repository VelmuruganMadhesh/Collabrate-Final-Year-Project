from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from app.core.logging import get_logger


logger = get_logger(__name__)


async def get_account_details(db, *, user_id: str) -> dict:
    accounts_col = db["accounts"]
    account = await accounts_col.find_one({"user_id": user_id})
    if not account:
        logger.warning("Account not found user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    logger.debug("Account found user_id=%s account_number=%s", user_id, account.get("account_number"))
    return {
        "account_number": account.get("account_number"),
        "currency": account.get("currency", "INR"),
        "balance": float(account.get("balance", 0.0)),
        "created_at": account.get("created_at"),
    }

