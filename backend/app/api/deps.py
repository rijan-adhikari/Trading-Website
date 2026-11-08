"""
Shared FastAPI dependencies. `get_current_user` is the ONLY way any route
derives "who is making this request" — routes and services must never
accept a user_id from the request body/query params and trust it.
"""
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.errors import ForbiddenError, UnauthorizedError
from app.utils.security import InvalidTokenError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token.")

    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise UnauthorizedError("User no longer exists.")
    if not user.is_active:
        raise UnauthorizedError("This account has been suspended.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required.")
    return user


def get_client_ip(request: Request) -> str | None:
    # Trust the ASGI peer address. Uvicorn's trusted proxy handling should
    # rewrite this to the client IP behind Render; never parse raw XFF here.
    return request.client.host if request.client else None
