import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import UserAccount, School
    from app.models.curriculum import CurriculumSubject
    from app.models.assessment import StudentMastery


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    school_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False)
    roll_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["UserAccount"] = relationship("UserAccount", back_populates="student_profile")
    school: Mapped[Optional["School"]] = relationship("School")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="student", cascade="all, delete-orphan"
    )
    masteries: Mapped[List["StudentMastery"]] = relationship(
        "StudentMastery", back_populates="student", cascade="all, delete-orphan"
    )


class ClassSection(Base):
    __tablename__ = "class_sections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_year: Mapped[str] = mapped_column(String(20), default="2026-27", nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    school: Mapped["School"] = relationship("School")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="section", cascade="all, delete-orphan"
    )
    teacher_assignments: Mapped[List["TeacherAssignment"]] = relationship(
        "TeacherAssignment", back_populates="section", cascade="all, delete-orphan"
    )


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="enrollments")
    section: Mapped["ClassSection"] = relationship("ClassSection", back_populates="enrollments")


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_class_teacher: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    teacher: Mapped["UserAccount"] = relationship("UserAccount", foreign_keys=[teacher_user_id])
    section: Mapped["ClassSection"] = relationship("ClassSection", back_populates="teacher_assignments")
    subject: Mapped[Optional["CurriculumSubject"]] = relationship("CurriculumSubject")


class ParentChildLink(Base):
    __tablename__ = "parent_child_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    parent_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(50), default="parent")  # father, mother, guardian
    consent_given: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    parent: Mapped["UserAccount"] = relationship("UserAccount", foreign_keys=[parent_user_id])
    student: Mapped["StudentProfile"] = relationship("StudentProfile", foreign_keys=[student_id])

    @property
    def relationship(self) -> str:
        return self.relation_type
