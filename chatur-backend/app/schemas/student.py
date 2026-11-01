from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class StudentSummary(BaseModel):
    id: str
    name: str
    grade: int
    section: str
    total_xp: int
    current_streak: int

    model_config = ConfigDict(from_attributes=True)


class EnrolledSubjectSummary(BaseModel):
    subject_id: str
    subject_name: str
    grade: int
    concepts_in_progress: int


class MasterySummaryItem(BaseModel):
    concept_id: str
    concept_name: str
    p_know: float
    working_level_name: str


class StudentDashboardResponse(BaseModel):
    student: StudentSummary
    enrolled_subjects: List[EnrolledSubjectSummary]
    mastery_summary: List[MasterySummaryItem]
    upcoming_assessments: List[Any] = []
    recent_achievements: List[Any] = []


class StudentMasteryResponse(BaseModel):
    id: str
    concept_id: str
    concept_code: str
    concept_name: str
    grade: int
    p_know: float
    level_name: str
    total_attempts: int
    total_correct: int
    last_assessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConceptChainNode(BaseModel):
    id: str
    code: str
    name_en: str
    grade: int
    p_know: Optional[float] = None
    level_name: Optional[str] = None
    is_mastered: bool = False


class ConceptChainResponse(BaseModel):
    target_concept_id: str
    target_concept_name: str
    chain: List[ConceptChainNode]


class ExplanationStyleItem(BaseModel):
    title: str
    content: str


class ComprehensionCheckItem(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    explanation: str


class ActiveLessonResponse(BaseModel):
    concept_id: str
    concept_name: str
    grade: int
    subject_name: str
    working_level_name: Optional[str] = None
    is_foundation_path: bool = False
    key_terms: List[str] = []
    styles: dict[str, ExplanationStyleItem]
    comprehension_check: ComprehensionCheckItem


class PracticeQuestionDTO(BaseModel):
    id: str
    concept_id: str
    concept_name: str
    difficulty: float
    difficulty_label: str
    body: str
    options: List[str]
    hints: List[str]


class PracticeNextResponse(BaseModel):
    question: PracticeQuestionDTO
    streak: int
    xp: int


class PracticeSubmitRequest(BaseModel):
    question_id: str
    selected_option: int
    hints_used: int = 0


class PracticeSubmitResponse(BaseModel):
    is_correct: bool
    correct_index: int
    explanation: str
    error_type: Optional[str] = None
    new_p_know: float
    earned_xp: int
    current_streak: int


class TestItemDTO(BaseModel):
    question_id: str
    concept_id: str
    concept_name: str
    section_type: str
    question_text: str
    options: List[str]


class ActiveTestResponse(BaseModel):
    assessment_id: str
    title: str
    time_limit_mins: int
    total_questions: int
    items: List[TestItemDTO]


class TestSingleResponse(BaseModel):
    question_id: str
    selected_option: int


class TestSubmitRequest(BaseModel):
    assessment_id: Optional[str] = None
    responses: List[TestSingleResponse]


class TestSubmitResultResponse(BaseModel):
    score: int
    max_score: int
    accuracy_pct: int
    feedback_message: str
    prerequisite_diagnosed: Optional[str] = None
    proposal_sent_to_teacher: bool

