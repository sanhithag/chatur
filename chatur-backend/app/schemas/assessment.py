from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class QuestionCreate(BaseModel):
    concept_id: str
    qtype: str = "mcq"
    difficulty: float = 0.5
    usage_tag: str = "practice"
    bloom_level: str = "understand"
    body_en: Dict[str, Any]
    body_te: Optional[Dict[str, Any]] = None
    body_hi: Optional[Dict[str, Any]] = None
    answer_data: Dict[str, Any]
    explanation_en: Optional[str] = None
    explanation_te: Optional[str] = None
    explanation_hi: Optional[str] = None
    hints: Optional[List[str]] = None


class QuestionResponse(BaseModel):
    id: str
    concept_id: str
    qtype: str
    difficulty: float
    usage_tag: str
    bloom_level: str
    body_en: Dict[str, Any]
    body_te: Optional[Dict[str, Any]] = None
    body_hi: Optional[Dict[str, Any]] = None
    answer_data: Dict[str, Any]
    explanation_en: Optional[str] = None
    explanation_te: Optional[str] = None
    explanation_hi: Optional[str] = None
    hints: Optional[List[str]] = None
    source: str
    approval_status: str
    attempt_count: int
    correct_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LevelProposalResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    target_concept_id: str
    target_concept_name: str
    proposed_level_concept_id: str
    proposed_level_concept_name: str
    proposal_type: str
    evidence: Optional[Dict[str, Any]] = None
    narrative_en: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProposalDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    teacher_notes: Optional[str] = None
    time_spent_secs: Optional[int] = 0


class ContentDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    notes: Optional[str] = None
