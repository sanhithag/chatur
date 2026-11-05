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
    pending_tasks: List[Any] = []


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
    subject_id: Optional[str] = None
    lesson_source: str = "legacy"  # stored | legacy | pending
    language_served: str = "en"
    translation_fallback: bool = False  # True => English shown because translation unavailable
    extra: Optional[dict] = None
    prerequisites: List[dict] = []
    related_concepts: List[dict] = []


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
    attempt_id: Optional[str] = None
    score: int
    max_score: int
    accuracy_pct: int
    feedback_message: str
    prerequisite_diagnosed: Optional[str] = None
    proposal_sent_to_teacher: bool


# ─── ADVANCED PRACTICE & TEST SCHEMAS ─────────────────────────────────────────

class FilterTopicItem(BaseModel):
    id: str
    topic_no: int
    name: str


class FilterChapterItem(BaseModel):
    id: str
    chapter_no: int
    name: str
    topics: List[FilterTopicItem] = []


class FilterSubjectItem(BaseModel):
    id: str
    code: str
    name: str
    domain: str
    chapters: List[FilterChapterItem] = []


class FilterGradeItem(BaseModel):
    grade: int
    subjects: List[FilterSubjectItem] = []


class PracticeFilterOptionsResponse(BaseModel):
    grades: List[FilterGradeItem] = []


class PracticeSessionRequest(BaseModel):
    grade: Optional[int] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None
    difficulty: Optional[str] = "all"  # all, easy, medium, hard
    count: int = 5
    lang: str = "en"


class PracticeSessionQuestion(BaseModel):
    id: str
    concept_id: str
    concept_name: str
    difficulty: float
    difficulty_label: str
    body: str
    options: List[str]
    hints: List[str]


class PracticeSessionResponse(BaseModel):
    session_id: str
    title: str
    total_questions: int
    difficulty: str
    questions: List[PracticeSessionQuestion]
    streak: int
    xp: int


class PracticeAnswerSubmission(BaseModel):
    question_id: str
    selected_option: int
    hints_used: int = 0
    time_spent_secs: int = 0


class PracticeSessionSubmitRequest(BaseModel):
    session_id: Optional[str] = None
    responses: List[PracticeAnswerSubmission]


class PracticeQuestionReview(BaseModel):
    question_id: str
    concept_id: str
    concept_name: str
    question_text: str
    options: List[str]
    selected_option: int
    correct_option: int
    is_correct: bool
    explanation: str


class PracticeSessionSubmitResponse(BaseModel):
    attempt_id: str
    score: int
    total: int
    accuracy_pct: int
    earned_xp: int
    new_total_xp: int
    current_streak: int
    results: List[PracticeQuestionReview]


class PracticeHistoryItem(BaseModel):
    attempt_id: str
    date: datetime
    title: str
    score: int
    max_score: int
    accuracy_pct: int
    time_spent_mins: int


class TestOverviewItem(BaseModel):
    id: str
    title: str
    assessment_type: str
    time_limit_mins: int
    total_questions: int
    subjects_covered: List[str] = []
    status: str = "available"  # available, completed, upcoming
    scheduled_for: Optional[datetime] = None


class TestHistoryItem(BaseModel):
    attempt_id: str
    assessment_id: str
    title: str
    score: float
    max_score: float
    accuracy_pct: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str


class TestListResponse(BaseModel):
    available: List[TestOverviewItem]
    upcoming: List[TestOverviewItem]
    history: List[TestHistoryItem]


class TestQuestionReviewItem(BaseModel):
    question_id: str
    concept_id: str
    concept_name: str
    section_type: str
    question_text: str
    options: List[str]
    selected_option: Optional[int] = None
    correct_option: int
    is_correct: bool
    explanation: str


class TestAttemptReviewResponse(BaseModel):
    attempt_id: str
    assessment_id: str
    title: str
    score: float
    max_score: float
    accuracy_pct: int
    time_taken_mins: int
    completed_at: datetime
    questions: List[TestQuestionReviewItem]


# ─── PROGRESS ANALYTICS SCHEMAS ───────────────────────────────────────────────

class SubjectProgressItem(BaseModel):
    subject_id: str
    subject_name: str
    domain: str
    total_concepts: int
    mastered_concepts: int
    in_progress_concepts: int
    needs_attention_concepts: int
    avg_mastery_pct: int


class StudentProgressSummaryResponse(BaseModel):
    total_xp: int
    current_streak: int
    longest_streak: int
    overall_mastery_pct: int
    total_concepts: int
    mastered_count: int
    learning_count: int
    needs_attention_count: int
    subjects: List[SubjectProgressItem]
    recent_activities: List[Any] = []


# ─── STUDENT TASK (TO-DO) SCHEMAS ─────────────────────────────────────────────

class StudentTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: str = "manual"  # manual, lesson, practice, test, revision
    link_type: Optional[str] = None  # chapter, topic, concept, practice, test
    link_id: Optional[str] = None
    link_payload: Optional[dict] = None
    due_date: Optional[datetime] = None


class StudentTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class StudentTaskResponse(BaseModel):
    id: str
    student_id: str
    title: str
    description: Optional[str] = None
    task_type: str
    link_type: Optional[str] = None
    link_id: Optional[str] = None
    link_payload: Optional[dict] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


