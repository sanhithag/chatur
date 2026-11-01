import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment import Question, LearningResource, StudentMastery


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subjects: Mapped[List["CurriculumSubject"]] = relationship(
        "CurriculumSubject", back_populates="board", cascade="all, delete-orphan"
    )


class CurriculumSubject(Base):
    __tablename__ = "curriculum_subjects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    board_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)  # mathematics, science, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    board: Mapped["Board"] = relationship("Board", back_populates="subjects")
    units: Mapped[List["CurriculumUnit"]] = relationship(
        "CurriculumUnit", back_populates="subject", cascade="all, delete-orphan"
    )


class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), default="2026-27")
    unit_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subject: Mapped["CurriculumSubject"] = relationship("CurriculumSubject", back_populates="units")
    chapters: Mapped[List["CurriculumChapter"]] = relationship(
        "CurriculumChapter", back_populates="unit", cascade="all, delete-orphan"
    )


class CurriculumChapter(Base):
    __tablename__ = "curriculum_chapters"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    unit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ncert_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    unit: Mapped["CurriculumUnit"] = relationship("CurriculumUnit", back_populates="chapters")
    topics: Mapped[List["CurriculumTopic"]] = relationship(
        "CurriculumTopic", back_populates="chapter", cascade="all, delete-orphan"
    )


class CurriculumTopic(Base):
    __tablename__ = "curriculum_topics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chapter: Mapped["CurriculumChapter"] = relationship("CurriculumChapter", back_populates="topics")
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept", back_populates="topic", cascade="all, delete-orphan"
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    topic_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("curriculum_topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_band: Mapped[str] = mapped_column(String(50), default="medium")  # easy, medium, hard
    learning_objectives: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    common_misconceptions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    content_status: Mapped[str] = mapped_column(String(50), default="approved")  # draft, approved, review
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    topic: Mapped[Optional["CurriculumTopic"]] = relationship("CurriculumTopic", back_populates="concepts")
    prerequisites: Mapped[List["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    dependent_concepts: Mapped[List["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="concept", cascade="all, delete-orphan"
    )
    resources: Mapped[List["LearningResource"]] = relationship(
        "LearningResource", back_populates="concept", cascade="all, delete-orphan"
    )
    masteries: Mapped[List["StudentMastery"]] = relationship(
        "StudentMastery",
        foreign_keys="StudentMastery.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan"
    )


class ConceptPrerequisite(Base):
    __tablename__ = "concept_prerequisites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prerequisite_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_strict: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    concept: Mapped["Concept"] = relationship(
        "Concept", foreign_keys=[concept_id], back_populates="prerequisites"
    )
    prerequisite: Mapped["Concept"] = relationship(
        "Concept", foreign_keys=[prerequisite_id], back_populates="dependent_concepts"
    )
