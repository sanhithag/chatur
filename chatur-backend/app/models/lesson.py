"""Structured lesson content + translation cache (additive; existing tables untouched)."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

LESSON_STATUSES = ("draft", "generated", "validated", "approved")


def _now():
    return datetime.now(timezone.utc)


class ConceptLesson(Base):
    """One English source lesson per (concept, version). Only 'approved' lessons reach students."""
    __tablename__ = "concept_lessons"
    __table_args__ = (UniqueConstraint("concept_id", "version", name="uq_lesson_concept_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON)  # see app/services/lesson_schema.py
    status: Mapped[str] = mapped_column(String(20), default="generated", index=True)
    validation_report: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class LessonTranslation(Base):
    """Cache keyed by (lesson, language); stale when source_version != lesson.version."""
    __tablename__ = "lesson_translations"
    __table_args__ = (UniqueConstraint("lesson_id", "lang", name="uq_translation_lesson_lang"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("concept_lessons.id", ondelete="CASCADE"), index=True)
    lang: Mapped[str] = mapped_column(String(5), index=True)
    source_version: Mapped[int] = mapped_column(Integer)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class GenerationLog(Base):
    __tablename__ = "content_generation_log"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(30))  # generate | translate | validate
    ok: Mapped[int] = mapped_column(Integer, default=1)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
