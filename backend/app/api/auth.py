from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, limiter
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SuccessResponse[TokenResponse], status_code=201)
@limiter.limit(get_settings().RATE_LIMIT_REGISTER)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(payload, ip_address=get_client_ip(request))
    access_token, refresh_token = service.issue_tokens(user)
    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )
    )


@router.post("/login", response_model=SuccessResponse[TokenResponse])
@limiter.limit(get_settings().RATE_LIMIT_LOGIN)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(payload, ip_address=get_client_ip(request))
    access_token, refresh_token = service.issue_tokens(user)
    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )
    )


@router.post("/refresh", response_model=SuccessResponse[dict])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    access_token = service.refresh_access_token(payload.refresh_token)
    return SuccessResponse(data={"access_token": access_token, "token_type": "bearer"})


@router.post("/logout", response_model=SuccessResponse[dict])
def logout(user: User = Depends(get_current_user)):
    # Stateless JWTs: logout is enforced client-side (discard tokens).
    # A future version can maintain a refresh-token denylist if needed.
    return SuccessResponse(data={"message": "Logged out."})


@router.get("/me", response_model=SuccessResponse[UserResponse])
def me(user: User = Depends(get_current_user)):
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.post("/change-password", response_model=SuccessResponse[dict])
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.change_password(user, payload.current_password, payload.new_password, ip_address=get_client_ip(request))
    return SuccessResponse(data={"message": "Password updated."})
