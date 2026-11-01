import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import UserAccount, School
    from app.models.student import StudentProfile
    from app.models.curriculum import Concept


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    qtype: Mapped[str] = mapped_column(String(50), default="mcq")  # mcq, numerical, subjective
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    usage_tag: Mapped[str] = mapped_column(String(50), default="practice")  # diagnostic, practice, test
    bloom_level: Mapped[str] = mapped_column(String(50), default="understand")  # remember, understand, apply, analyze
    body_en: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # {"text": "..."}
    body_te: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    body_hi: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    answer_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # {"correct_index": 0, "options": [...]}
    primary_error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    explanation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_te: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hints: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="ncert")
    approval_status: Mapped[str] = mapped_column(
        String(50), default="approved", index=True
    )  # approved, pending_review, rejected
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    concept: Mapped["Concept"] = relationship("Concept", back_populates="questions")


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rtype: Mapped[str] = mapped_column(
        String(50), default="explainer"
    )  # explainer, video, simulation, interactive
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    title_te: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_te: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_secs: Mapped[int] = mapped_column(Integer, default=180)
    approval_status: Mapped[str] = mapped_column(
        String(50), default="approved"
    )  # approved, pending_review, rejected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    concept: Mapped["Concept"] = relationship("Concept", back_populates="resources")


class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    p_know: Mapped[float] = mapped_column(Float, default=0.1)
    p_learn: Mapped[float] = mapped_column(Float, default=0.2)
    p_guess: Mapped[float] = mapped_column(Float, default=0.2)
    p_slip: Mapped[float] = mapped_column(Float, default=0.1)
    working_concept_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    recent_scores: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_low: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_high: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="masteries")
    concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[concept_id], back_populates="masteries")
    working_concept: Mapped[Optional["Concept"]] = relationship("Concept", foreign_keys=[working_concept_id])
    history: Mapped[List["MasteryHistory"]] = relationship(
        "MasteryHistory", back_populates="mastery", cascade="all, delete-orphan"
    )


class MasteryHistory(Base):
    __tablename__ = "mastery_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    mastery_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_mastery.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    p_know_before: Mapped[float] = mapped_column(Float, nullable=False)
    p_know_after: Mapped[float] = mapped_column(Float, nullable=False)
    trigger_event: Mapped[str] = mapped_column(
        String(50), default="question_response"
    )  # question_response, diagnostic, teacher_override
    answer_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    mastery: Mapped["StudentMastery"] = relationship("StudentMastery", back_populates="history")


class LevelChangeProposal(Base):
    __tablename__ = "level_change_proposals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposed_level_concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposal_type: Mapped[str] = mapped_column(
        String(50), default="remediation"
    )  # remediation, acceleration
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    narrative_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    narrative_te: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    narrative_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # pending, approved, rejected, expired
    decided_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    teacher_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    target_concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[target_concept_id])
    proposed_level_concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[proposed_level_concept_id])
    decider: Mapped[Optional["UserAccount"]] = relationship("UserAccount", foreign_keys=[decided_by])


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    school_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        String(50), default="diagnostic"
    )  # diagnostic, formative, summative
    concept_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    total_marks: Mapped[float] = mapped_column(Float, default=100.0)
    time_limit_mins: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    attempts: Mapped[List["AssessmentAttempt"]] = relationship(
        "AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="in_progress"
    )  # in_progress, completed, abandoned
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="attempts")
    responses: Mapped[List["AttemptResponse"]] = relationship(
        "AttemptResponse", back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptResponse(Base):
    __tablename__ = "attempt_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    points_awarded: Mapped[float] = mapped_column(Float, default=0.0)
    time_spent_secs: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="responses")
    question: Mapped["Question"] = relationship("Question")
