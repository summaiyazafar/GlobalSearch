from fastapi import APIRouter, Depends

from app.models.user import User
from app.security.auth import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me")
async def get_my_account(
    current_user: User = Depends(get_current_user),
):
    """
    Return the currently authenticated user's basic account details.
    """

    return {
        "success": True,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "email_verified": current_user.email_verified,
        },
    }