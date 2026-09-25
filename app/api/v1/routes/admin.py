from fastapi import APIRouter, Depends

from app.api.dependencies import require_role
from app.models.user import User


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/test")
def admin_test(
    current_user: User = Depends(require_role("admin")),
):
    return {
        "message": "Welcome, admin",
        "user_id": current_user.id,
        "email": current_user.email,
    }