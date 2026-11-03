from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


async def get_supabase_user(
    access_token: str,
) -> dict:
    """
    Validate an access token through Supabase Auth.

    The token is sent to Supabase's authenticated user endpoint.
    The backend does not trust user IDs supplied by the client.
    """

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured.",
        )

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.AUTH_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(url, headers=headers)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timed out.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to authentication service.",
        )

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned an unexpected response.",
        )

    try:
        user_data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Invalid response from authentication service.",
        )

    if not isinstance(user_data, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication response.",
        )

    if not user_data.get("id") or not user_data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated account is missing required information.",
        )

    return user_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Supabase token and get or create the local user record.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required.",
        )

    supabase_user = await get_supabase_user(credentials.credentials)

    try:
        user_id = UUID(str(supabase_user["id"]))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account identifier.",
        )

    email = str(supabase_user["email"]).strip().lower()

    metadata = supabase_user.get("user_metadata") or {}

    full_name = (
        metadata.get("full_name")
        or metadata.get("name")
        or email.split("@")[0]
    )

    email_verified = bool(supabase_user.get("email_confirmed_at"))

    try:
        user = db.scalar(
            select(User).where(User.id == user_id)
        )

        if user is None:
            user = User(
                id=user_id,
                email=email,
                full_name=full_name,
                is_active=True,
                email_verified=email_verified,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        else:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account has been disabled.",
                )

            changed = False

            if user.email != email:
                user.email = email
                changed = True

            if not user.full_name and full_name:
                user.full_name = full_name
                changed = True

            if user.email_verified != email_verified:
                user.email_verified = email_verified
                changed = True

            if changed:
                db.commit()
                db.refresh(user)

        return user

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load the local user account.",
        )