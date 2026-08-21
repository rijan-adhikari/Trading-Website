from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import AdminUserUpdateRequest, UserResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=SuccessResponse[list[UserResponse]])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return SuccessResponse(data=[UserResponse.model_validate(user) for user in users])


@router.patch("/users/{user_id}", response_model=SuccessResponse[UserResponse])
def update_user_status(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        from app.utils.errors import NotFoundError

        raise NotFoundError("User not found.")
    if user.id == admin.id and not payload.is_active:
        from app.utils.errors import ValidationAPIError

        raise ValidationAPIError("You cannot suspend your own admin account.")

    user.is_active = payload.is_active
    AuditService(db).log(
        action="USER_STATUS_UPDATED",
        user_id=admin.id,
        entity_type="user",
        entity_id=user.id,
        metadata={"is_active": payload.is_active},
    )
    db.commit()
    db.refresh(user)
    return SuccessResponse(data=UserResponse.model_validate(user))