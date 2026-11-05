from fastapi import Depends, HTTPException, status

from app.core.config import settings
from app.models.user import User
from app.security.auth import get_current_user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    allowed_emails = {
        email.strip().lower()
        for email in settings.ADMIN_EMAILS
        if email.strip()
    }

    user_email = (current_user.email or "").strip().lower()

    if not allowed_emails or user_email not in allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator permission is required.",
        )

    return current_user