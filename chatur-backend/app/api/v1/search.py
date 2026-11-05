from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.models.assessment import LearningResource, Question
from app.models.curriculum import (
    Board,
    Concept,
    CurriculumChapter,
    CurriculumSubject,
    CurriculumTopic,
    CurriculumUnit,
)
from app.models.user import UserAccount

router = APIRouter()


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    lang: str = Query("en", description="Language preference: en, te, hi"),
    grade: Optional[int] = Query(None, description="Optional grade filter 6-10"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> Dict[str, Any]:
    term = f"%{q.strip()}%"

    # 1. Subjects
    subj_stmt = (
        select(CurriculumSubject)
        .where(
            CurriculumSubject.is_active.is_(True),
            or_(
                CurriculumSubject.name_en.ilike(term),
                CurriculumSubject.name_te.ilike(term),
                CurriculumSubject.name_hi.ilike(term),
                CurriculumSubject.code.ilike(term),
                CurriculumSubject.domain.ilike(term),
            ),
        )
        .order_by(CurriculumSubject.sort_order)
        .limit(10)
    )
    subj_rows = (await db.execute(subj_stmt)).scalars().all()
    subjects = [
        {
            "id": s.id,
            "category": "subject",
            "title": (s.name_te if lang == "te" and s.name_te else None)
            or (s.name_hi if lang == "hi" and s.name_hi else None)
            or s.name_en,
            "code": s.code,
            "domain": s.domain,
            "subtitle": f"{s.domain.capitalize()} • CBSE Curriculum",
            "url": f"/student/learn?subject_id={s.id}",
        }
        for s in subj_rows
    ]

    # 2. Chapters
    chap_stmt = (
        select(CurriculumChapter, CurriculumUnit, CurriculumSubject)
        .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .join(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .where(
            or_(
                CurriculumChapter.name_en.ilike(term),
                CurriculumChapter.name_te.ilike(term),
                CurriculumChapter.name_hi.ilike(term),
            )
        )
    )
    if grade is not None:
        chap_stmt = chap_stmt.where(CurriculumUnit.grade == grade)
    chap_stmt = chap_stmt.order_by(CurriculumChapter.chapter_no).limit(10)
    chap_rows = (await db.execute(chap_stmt)).all()
    chapters = [
        {
            "id": ch.id,
            "category": "chapter",
            "chapter_no": ch.chapter_no,
            "title": (ch.name_te if lang == "te" and ch.name_te else None)
            or (ch.name_hi if lang == "hi" and ch.name_hi else None)
            or ch.name_en,
            "grade": u.grade,
            "subject_id": s.id,
            "subject_name": s.name_en,
            "subtitle": f"Class {u.grade} • {s.name_en} • Chapter {ch.chapter_no}",
            "url": f"/student/learn?subject_id={s.id}&grade={u.grade}&chapter_id={ch.id}",
        }
        for ch, u, s in chap_rows
    ]

    # 3. Topics
    topic_stmt = (
        select(CurriculumTopic, CurriculumChapter, CurriculumUnit, CurriculumSubject)
        .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .join(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .where(
            or_(
                CurriculumTopic.name_en.ilike(term),
                CurriculumTopic.name_te.ilike(term),
                CurriculumTopic.name_hi.ilike(term),
            )
        )
    )
    if grade is not None:
        topic_stmt = topic_stmt.where(CurriculumUnit.grade == grade)
    topic_stmt = topic_stmt.order_by(CurriculumTopic.topic_no).limit(10)
    topic_rows = (await db.execute(topic_stmt)).all()
    topics = [
        {
            "id": t.id,
            "category": "topic",
            "title": (t.name_te if lang == "te" and t.name_te else None)
            or (t.name_hi if lang == "hi" and t.name_hi else None)
            or t.name_en,
            "grade": u.grade,
            "subject_id": s.id,
            "chapter_id": ch.id,
            "subtitle": f"Class {u.grade} • {s.name_en} • {ch.name_en}",
            "url": f"/student/learn?subject_id={s.id}&grade={u.grade}&chapter_id={ch.id}&topic_id={t.id}",
        }
        for t, ch, u, s in topic_rows
    ]

    # 4. Concepts
    concept_stmt = (
        select(Concept, CurriculumTopic, CurriculumChapter, CurriculumUnit, CurriculumSubject)
        .outerjoin(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
        .outerjoin(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .outerjoin(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .outerjoin(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .where(
            Concept.is_active.is_(True),
            or_(
                Concept.name_en.ilike(term),
                Concept.name_te.ilike(term),
                Concept.name_hi.ilike(term),
                Concept.code.ilike(term),
            ),
        )
    )
    if grade is not None:
        concept_stmt = concept_stmt.where(Concept.grade == grade)
    concept_stmt = concept_stmt.order_by(Concept.grade, Concept.sort_order).limit(15)
    concept_rows = (await db.execute(concept_stmt)).all()
    concepts = [
        {
            "id": c.id,
            "category": "concept",
            "code": c.code,
            "title": (c.name_te if lang == "te" and c.name_te else None)
            or (c.name_hi if lang == "hi" and c.name_hi else None)
            or c.name_en,
            "grade": c.grade,
            "difficulty": c.difficulty_band,
            "subject_id": s.id if s else None,
            "subject_name": s.name_en if s else "General",
            "chapter_name": ch.name_en if ch else None,
            "subtitle": f"Class {c.grade} • {s.name_en if s else 'Curriculum'} • {ch.name_en if ch else c.difficulty_band.capitalize()}",
            "url": f"/student/learn?concept_id={c.id}",
            "practice_url": f"/student/practice?concept_id={c.id}",
        }
        for c, t, ch, u, s in concept_rows
    ]

    # 5. Learning Resources / Questions
    res_stmt = (
        select(LearningResource, Concept)
        .join(Concept, LearningResource.concept_id == Concept.id)
        .where(
            or_(
                LearningResource.title_en.ilike(term),
                LearningResource.content_en.ilike(term),
            )
        )
        .limit(8)
    )
    res_rows = (await db.execute(res_stmt)).all()
    materials = [
        {
            "id": r.id,
            "category": "material",
            "title": r.title_en,
            "rtype": r.rtype,
            "concept_id": c.id,
            "concept_name": c.name_en,
            "grade": c.grade,
            "subtitle": f"Learning Resource ({r.rtype}) • Class {c.grade} • {c.name_en}",
            "url": f"/student/learn?concept_id={c.id}",
        }
        for r, c in res_rows
    ]

    total = len(subjects) + len(chapters) + len(topics) + len(concepts) + len(materials)

    return {
        "query": q,
        "total": total,
        "categories": {
            "subjects": subjects,
            "chapters": chapters,
            "topics": topics,
            "concepts": concepts,
            "materials": materials,
        },
    }
