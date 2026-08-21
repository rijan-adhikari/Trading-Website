from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import NotificationType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="notifications")


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable trail for every sensitive action (auth events, trades,
    order cancellations, admin stock/config edits, balance adjustments).
    Never write passwords, tokens, or secrets into `metadata_`.
    """
    __tablename__ = "audit_logs"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON().with_variant(JSONB, "postgresql"), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User", back_populates="audit_logs")


class SystemSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Admin-editable overrides (initial balance, fee schedule, etc). The
    app.config.Settings values are the defaults/fallback; a row here, if
    present, takes precedence. Keeps "change fee config" an admin-panel
    action instead of a redeploy.
    """
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
