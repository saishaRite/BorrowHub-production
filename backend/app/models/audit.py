from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey,
    Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey("app_user.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(60), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    actor = relationship("AppUser")


class SystemJobLog(Base):
    __tablename__ = "system_job_log"

    job_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_name = Column(String(60), nullable=False)
    status = Column(SQLEnum("RUNNING", "COMPLETED", "FAILED", name="job_status"), nullable=False)
    records_processed = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
