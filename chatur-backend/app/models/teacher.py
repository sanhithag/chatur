import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import UserAccount
    from app.models.student import ClassSection, StudentProfile
    from app.models.curriculum import Concept


class RemedialGroup(Base):
    __tablename__ = "remedial_groups"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True
    )  # active, completed, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    teacher: Mapped["UserAccount"] = relationship("UserAccount", foreign_keys=[teacher_user_id])
    section: Mapped[Optional["ClassSection"]] = relationship("ClassSection")
    concept: Mapped["Concept"] = relationship("Concept")
    members: Mapped[List["RemedialGroupMember"]] = relationship(
        "RemedialGroupMember", back_populates="group", cascade="all, delete-orphan"
    )


class RemedialGroupMember(Base):
    __tablename__ = "remedial_group_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remedial_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    exit_p_know: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    group: Mapped["RemedialGroup"] = relationship("RemedialGroup", back_populates="members")
    student: Mapped["StudentProfile"] = relationship("StudentProfile")


class TeacherActivityLog(Base):
    __tablename__ = "teacher_activity_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # review_proposal, create_group, etc.
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    teacher: Mapped["UserAccount"] = relationship("UserAccount")


class Worksheet(Base):
    __tablename__ = "worksheets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # list of concept UUIDs
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    teacher: Mapped["UserAccount"] = relationship("UserAccount")
