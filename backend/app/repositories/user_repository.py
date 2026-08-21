from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        return self.db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def exists_by_email_or_username(self, email: str, username: str) -> bool:
        stmt = select(User).where(or_(User.email == email.lower(), User.username == username))
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()  # populate user.id without committing — caller controls the transaction
        return user
