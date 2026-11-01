import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import School, UserAccount
    from app.models.student import StudentProfile


class PilotCohort(Base):
    __tablename__ = "pilot_cohorts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_grade: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    school: Mapped["School"] = relationship("School")
    members: Mapped[List["PilotCohortMember"]] = relationship(
        "PilotCohortMember", back_populates="cohort", cascade="all, delete-orphan"
    )


class PilotCohortMember(Base):
    __tablename__ = "pilot_cohort_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cohort_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pilot_cohorts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    baseline_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    midline_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    endline_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cohort: Mapped["PilotCohort"] = relationship("PilotCohort", back_populates="members")
    student: Mapped["StudentProfile"] = relationship("StudentProfile")


class ImpactSnapshot(Base):
    __tablename__ = "impact_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cohort_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pilot_cohorts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    avg_mastery: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_active_students: Mapped[int] = mapped_column(Integer, default=0)
    learning_gain_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    school: Mapped["School"] = relationship("School")
    cohort: Mapped[Optional["PilotCohort"]] = relationship("PilotCohort")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
