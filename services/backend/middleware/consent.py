from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_db
from db.models import ConsentEvent, User
from middleware.rbac import CurrentUser, require_volunteer

logger = logging.getLogger(__name__)


async def get_consent_flags(user_id: str, db: AsyncSession) -> dict[str, bool]:
    stmt = select(User.consent_analytics, User.consent_personalization, User.consent_ai_training).where(User.id == user_id)
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        logger.warning("Consent lookup failed for missing user %s", user_id)
        return {"analytics": False, "personalization": False, "ai_training": False}
    analytics, personalization, ai_training = row
    return {
        "analytics": bool(analytics),
        "personalization": bool(personalization),
        "ai_training": bool(ai_training),
    }


async def audit_consent_access(
    user_id: str,
    scope: str,
    granted: bool,
    db: AsyncSession,
    source: str = "access",
) -> None:
    event = ConsentEvent(user_id=user_id, scope=scope, granted=granted, source=source)
    db.add(event)
    await db.flush()


async def require_ai_training_consent(
    user: CurrentUser = Depends(require_volunteer),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    flags = await get_consent_flags(user.user_id, db)
    granted = flags.get("ai_training", False)
    await audit_consent_access(user.user_id, "ai_training", granted, db, source="recommendations")
    if not granted:
        logger.warning("AI training access denied for user %s", user.user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI training consent required for this feature",
        )
    return user