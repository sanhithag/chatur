from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_db, require_role
from app.models import Concept, CurriculumChapter, CurriculumSubject, CurriculumTopic, CurriculumUnit
from app.models.lesson import ConceptLesson, LessonTranslation
from app.models.user import UserAccount
from app.services import ai_provider, lesson_service
from app.services.lesson_schema import validate_lesson

router = APIRouter()
admin_only = require_role("admin", "super_admin")


class StatusUpdate(BaseModel):
    status: str  # validated | approved | generated


@router.get("/coverage")
async def coverage(db: AsyncSession = Depends(get_db), _: UserAccount = Depends(admin_only)):
    """Exact coverage per subject+grade: concepts vs lessons by status vs translations."""
    base = (select(CurriculumSubject.name_en, Concept.grade, Concept.id)
            .join(CurriculumUnit, CurriculumUnit.subject_id == CurriculumSubject.id)
            .join(CurriculumChapter, CurriculumChapter.unit_id == CurriculumUnit.id)
            .join(CurriculumTopic, CurriculumTopic.chapter_id == CurriculumChapter.id)
            .join(Concept, Concept.topic_id == CurriculumTopic.id))
    rows = (await db.execute(base)).all()
    lessons = {}
    for cid, st, lid in (await db.execute(select(ConceptLesson.concept_id, ConceptLesson.status, ConceptLesson.id))).all():
        lessons.setdefault(cid, []).append((st, lid))
    trs = {}
    for lid, lang in (await db.execute(select(LessonTranslation.lesson_id, LessonTranslation.lang))).all():
        trs.setdefault(lid, set()).add(lang)
    out = {}
    for subj, grade, cid in rows:
        o = out.setdefault((subj, grade), {"subject": subj, "grade": grade, "concepts": 0, "with_lesson": 0, "validated": 0, "approved": 0, "translated_te": 0, "translated_hi": 0})
        o["concepts"] += 1
        ls = lessons.get(cid, [])
        if ls:
            o["with_lesson"] += 1
        if any(s in ("validated", "approved") for s, _ in ls): o["validated"] += 1
        if any(s == "approved" for s, _ in ls): o["approved"] += 1
        for _, lid in ls:
            if "te" in trs.get(lid, ()): o["translated_te"] += 1; break
        for _, lid in ls:
            if "hi" in trs.get(lid, ()): o["translated_hi"] += 1; break
    return sorted(out.values(), key=lambda x: (x["subject"], x["grade"]))


@router.get("/lessons")
async def list_lessons(status: Optional[str] = None, limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db), _: UserAccount = Depends(admin_only)):
    q = select(ConceptLesson, Concept.name_en, Concept.code).join(Concept, Concept.id == ConceptLesson.concept_id).order_by(ConceptLesson.updated_at.desc()).limit(limit)
    if status:
        q = q.where(ConceptLesson.status == status)
    return [{"id": l.id, "concept": n, "code": c, "version": l.version, "status": l.status, "validation": l.validation_report,
             "provider": l.provider, "content": l.content} for l, n, c in (await db.execute(q)).all()]


@router.post("/lessons/{lesson_id}/status")
async def set_status(lesson_id: str, body: StatusUpdate, db: AsyncSession = Depends(get_db), user: UserAccount = Depends(admin_only)):
    if body.status not in ("generated", "validated", "approved"):
        raise HTTPException(400, "status must be generated, validated or approved")
    lesson = await db.get(ConceptLesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    if body.status == "approved":
        report = validate_lesson(lesson.content)
        lesson.validation_report = report
        if not report["ok"]:
            raise HTTPException(422, {"message": "Lesson fails automatic checks", "issues": report["issues"]})
        lesson.approved_by = user.id
    lesson.status = body.status
    await db.commit()
    n = await lesson_service.sync_questions(db, lesson) if body.status == "approved" else 0
    return {"id": lesson.id, "status": lesson.status, "questions_synced": n}


@router.post("/generate/{concept_id}")
async def generate_one(concept_id: str, db: AsyncSession = Depends(get_db), _: UserAccount = Depends(admin_only)):
    if not ai_provider.is_configured():
        raise HTTPException(503, "No AI provider configured")
    row = (await db.execute(select(Concept, CurriculumTopic, CurriculumChapter, CurriculumSubject)
        .join(CurriculumTopic, Concept.topic_id == CurriculumTopic.id).join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id).join(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .where(Concept.id == concept_id))).first()
    if not row:
        raise HTTPException(404, "Concept not found")
    c, t, ch, s = row
    try:
        lesson = await lesson_service.generate_lesson(db, c, ch.name_en, t.name_en, s.name_en, "", [ch.source_ref or ""])
    except ai_provider.AIUnavailable as e:
        raise HTTPException(502, str(e))
    return {"id": lesson.id, "status": lesson.status, "validation": lesson.validation_report}
