from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.portfolio import Portfolio
from app.models.user import User
from app.models.watchlist import Watchlist
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, RegisterRequest
from app.services.audit_service import AuditService
from app.utils.errors import ConflictError, UnauthorizedError, ValidationAPIError
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.security import InvalidTokenError

settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def register(self, payload: RegisterRequest, ip_address: str | None = None) -> User:
        if self.users.exists_by_email_or_username(payload.email, payload.username):
            raise ConflictError("An account with this email or username already exists.")

        user = User(
            name=payload.name,
            username=payload.username,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
        )
        self.users.create(user)

        # Fund the new account and give it a default watchlist — every
        # user gets a Portfolio the moment they register, never lazily.
        portfolio = Portfolio(
            user_id=user.id,
            cash_balance=settings.INITIAL_VIRTUAL_BALANCE,
            initial_balance=settings.INITIAL_VIRTUAL_BALANCE,
            realized_pl=0,
        )
        self.db.add(portfolio)

        watchlist = Watchlist(user_id=user.id, name="My Watchlist", is_default=True)
        self.db.add(watchlist)

        self.audit.log(
            action="USER_REGISTERED",
            user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            metadata={"initial_balance": str(settings.INITIAL_VIRTUAL_BALANCE)},
            ip_address=ip_address,
        )

        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, payload: LoginRequest, ip_address: str | None = None) -> User:
        user = self.users.get_by_email(payload.email)

        if not user or not verify_password(payload.password, user.password_hash):
            self.audit.log(
                action="LOGIN_FAILED",
                user_id=user.id if user else None,
                entity_type="user",
                metadata={"email": payload.email},
                ip_address=ip_address,
            )
            self.db.commit()
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("This account has been suspended.")

        self.audit.log(
            action="LOGIN_SUCCESS", user_id=user.id, entity_type="user", entity_id=user.id, ip_address=ip_address
        )
        self.db.commit()
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        return create_access_token(user.id), create_refresh_token(user.id)

    def refresh_access_token(self, refresh_token: str) -> str:
        try:
            user_id = decode_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise UnauthorizedError(str(exc)) from exc

        user = self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Account is no longer active.")
        return create_access_token(user.id)

    def change_password(self, user: User, current_password: str, new_password: str, ip_address: str | None = None) -> None:
        if not verify_password(current_password, user.password_hash):
            raise ValidationAPIError("Current password is incorrect.")
        user.password_hash = hash_password(new_password)
        self.audit.log(
            action="PASSWORD_CHANGED", user_id=user.id, entity_type="user", entity_id=user.id, ip_address=ip_address
        )
        self.db.commit()
