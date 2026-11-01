from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClassSectionSummary(BaseModel):
    id: str
    grade: int
    section: str
    academic_year: str

    model_config = ConfigDict(from_attributes=True)


class ConceptGapItem(BaseModel):
    concept_id: str
    concept_name: str
    student_count: int


class StudentAttentionItem(BaseModel):
    student_id: str
    student_name: str
    gap_count: int


class TeacherDashboardResponse(BaseModel):
    section: Optional[ClassSectionSummary] = None
    total_students: int
    pending_proposals: int
    concepts_with_gaps: List[ConceptGapItem]
    students_needing_attention: List[StudentAttentionItem]


class HeatmapConceptItem(BaseModel):
    id: str
    code: str
    name_en: str
    grade: int


class HeatmapMasteryItem(BaseModel):
    concept_id: str
    p_know: float


class HeatmapStudentItem(BaseModel):
    student_id: str
    student_name: str
    grade: Optional[int] = None
    section: Optional[str] = None
    mastery: List[HeatmapMasteryItem] = []
    concept_mastery: List[HeatmapMasteryItem] = []


class TeacherHeatmapResponse(BaseModel):
    concepts: List[HeatmapConceptItem]
    students: List[HeatmapStudentItem]


class RemedialGroupCreate(BaseModel):
    name: str
    concept_id: str
    section_id: Optional[str] = None
    student_ids: List[str] = []
    description: Optional[str] = None


class RemedialGroupResponse(BaseModel):
    id: str
    name: str
    concept_id: str
    concept_name: str
    section_id: Optional[str] = None
    member_count: int
    status: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
