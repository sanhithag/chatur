from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class BoardResponse(BaseModel):
    id: str
    code: str
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubjectResponse(BaseModel):
    id: str
    board_id: str
    code: str
    name_en: str
    name_te: Optional[str] = None
    name_hi: Optional[str] = None
    domain: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TopicResponse(BaseModel):
    id: str
    chapter_id: str
    topic_no: int
    name_en: str
    name_te: Optional[str] = None
    name_hi: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChapterWithTopicsResponse(BaseModel):
    id: str
    unit_id: str
    chapter_no: int
    name_en: str
    name_te: Optional[str] = None
    name_hi: Optional[str] = None
    ncert_verified: bool
    topics: List[TopicResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConceptDetailResponse(BaseModel):
    id: str
    topic_id: Optional[str] = None
    code: str
    name_en: str
    name_te: Optional[str] = None
    name_hi: Optional[str] = None
    grade: int
    difficulty_band: str
    learning_objectives: Optional[List[str]] = None
    common_misconceptions: Optional[List[Dict[str, Any]]] = None
    content_status: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PrerequisiteItem(BaseModel):
    prerequisite_id: str
    code: str
    name_en: str
    grade: int
    is_strict: bool
    weight: float


class ConceptChainStep(BaseModel):
    id: str
    code: str
    name_en: str
    name_te: Optional[str] = None
    name_hi: Optional[str] = None
    grade: int
    difficulty_band: str


class CurriculumOverviewResponse(BaseModel):
    total_subjects: int
    total_units: int
    total_chapters: int
    total_concepts: int
    approved_questions: int
    pending_questions: int
    total_resources: int
