from uuid import UUID

from sqlalchemy.orm import Session

from app.models.system import AuditLog


class AuditService:
    """Every sensitive action in the app (auth events, trades, order
    cancellations, admin edits, balance adjustments) should call `log()`
    in the SAME db session/transaction as the action itself, so the audit
    record can never exist without — or be lost alongside — the action it
    describes. Never pass passwords, tokens, or secrets in `metadata`.
    """

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            metadata_=metadata,
            ip_address=ip_address,
        )
        self.db.add(entry)
        self.db.flush()
        return entry
