"""
Password hashing (Argon2) and JWT access/refresh token helpers.

Nothing outside this module should call Argon2 or PyJWT directly — route
handlers depend on `hash_password`, `verify_password`, `create_access_token`,
`create_refresh_token`, and `decode_token`.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from app.config import get_settings

settings = get_settings()

# Argon2id is the password-hashing algorithm for this application.
password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, plain_password)
    except VerificationError:
        return False


def _create_token(subject: str, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID) -> str:
    return _create_token(str(user_id), timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(str(user_id), timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: Literal["access", "refresh"] = "access") -> UUID:
    """Returns the user_id encoded in the token, or raises InvalidTokenError."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token")

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token missing subject")

    try:
        return UUID(sub)
    except ValueError as exc:
        raise InvalidTokenError("Token subject is not a valid user id") from exc
