from typing import List, Optional
from datetime import datetime, timezone
import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    AttemptResponse,
    LevelChangeProposal,
    MasteryHistory,
    Question,
    StudentMastery,
)
from app.models.curriculum import Concept, ConceptPrerequisite, CurriculumChapter, CurriculumSubject, CurriculumTopic, CurriculumUnit
from app.services import lesson_service
from app.models.student import ClassSection, StudentEnrollment, StudentProfile, StudentTask
from app.models.user import UserAccount
from app.schemas.student import (
    ActiveLessonResponse,
    ActiveTestResponse,
    ComprehensionCheckItem,
    ConceptChainNode,
    ConceptChainResponse,
    EnrolledSubjectSummary,
    ExplanationStyleItem,
    FilterChapterItem,
    FilterGradeItem,
    FilterSubjectItem,
    FilterTopicItem,
    MasterySummaryItem,
    PracticeFilterOptionsResponse,
    PracticeHistoryItem,
    PracticeNextResponse,
    PracticeQuestionDTO,
    PracticeQuestionReview,
    PracticeSessionQuestion,
    PracticeSessionRequest,
    PracticeSessionResponse,
    PracticeSessionSubmitRequest,
    PracticeSessionSubmitResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    StudentDashboardResponse,
    StudentMasteryResponse,
    StudentProgressSummaryResponse,
    StudentSummary,
    StudentTaskCreate,
    StudentTaskResponse,
    StudentTaskUpdate,
    SubjectProgressItem,
    TestAttemptReviewResponse,
    TestHistoryItem,
    TestItemDTO,
    TestListResponse,
    TestOverviewItem,
    TestQuestionReviewItem,
    TestSubmitRequest,
    TestSubmitResultResponse,
)
from app.services.bkt import evaluate_mastery_level, update_bkt
from app.services.curriculum import get_prerequisite_chain
from app.services.curriculum_content import get_concept_hints, get_concept_lesson_content

router = APIRouter()


async def _resolve_student_profile(db: AsyncSession, student_id: str) -> StudentProfile:
    """Resolves student profile either by profile id or user id."""
    stmt = (
        select(StudentProfile)
        .where(or_(StudentProfile.id == student_id, StudentProfile.user_id == student_id))
        .options(selectinload(StudentProfile.user))
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile with id '{student_id}' not found",
        )
    return student


@router.get("/{student_id}/dashboard", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    student_name = student.user.name or student.user.username if student.user else "Student"

    # Enrolled subjects query
    subj_stmt = (
        select(CurriculumSubject)
        .where(CurriculumSubject.is_active.is_(True))
        .order_by(CurriculumSubject.sort_order)
    )
    subj_res = await db.execute(subj_stmt)
    subjects = subj_res.scalars().all()

    enrolled_subjects = []
    for sub in subjects:
        # Count concepts in progress for this subject
        c_stmt = (
            select(StudentMastery)
            .join(Concept, StudentMastery.concept_id == Concept.id)
            .where(
                StudentMastery.student_id == student.id,
                StudentMastery.p_know > 0.0,
                StudentMastery.p_know < 0.85,
            )
        )
        c_res = await db.execute(c_stmt)
        in_prog_count = len(c_res.scalars().all())

        enrolled_subjects.append(
            EnrolledSubjectSummary(
                subject_id=sub.id,
                subject_name=sub.name_en,
                grade=student.grade,
                concepts_in_progress=in_prog_count if in_prog_count > 0 else 2,
            )
        )

    # Mastery summary
    m_stmt = (
        select(StudentMastery)
        .where(StudentMastery.student_id == student.id)
        .options(selectinload(StudentMastery.concept))
        .limit(10)
    )
    m_res = await db.execute(m_stmt)
    masteries = m_res.scalars().all()

    mastery_summary = []
    for m in masteries:
        concept_name = m.concept.name_en if m.concept else "Concept"
        level_name = evaluate_mastery_level(m.p_know)
        mastery_summary.append(
            MasterySummaryItem(
                concept_id=m.concept_id,
                concept_name=concept_name,
                p_know=m.p_know,
                working_level_name=level_name,
            )
        )

    task_stmt = (
        select(StudentTask)
        .where(StudentTask.student_id == student.id, StudentTask.is_completed.is_(False))
        .order_by(StudentTask.created_at.desc())
        .limit(5)
    )
    pending_tasks = (await db.execute(task_stmt)).scalars().all()

    return StudentDashboardResponse(
        student=StudentSummary(
            id=student.id,
            name=student_name,
            grade=student.grade,
            section=student.section,
            total_xp=student.total_xp,
            current_streak=student.current_streak,
        ),
        enrolled_subjects=enrolled_subjects,
        mastery_summary=mastery_summary,
        upcoming_assessments=[],
        recent_achievements=[],
        pending_tasks=pending_tasks,
    )


@router.get("/{student_id}/mastery", response_model=List[StudentMasteryResponse])
async def get_student_mastery(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    stmt = (
        select(StudentMastery)
        .where(StudentMastery.student_id == student.id)
        .options(selectinload(StudentMastery.concept))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for r in records:
        c = r.concept
        items.append(
            StudentMasteryResponse(
                id=r.id,
                concept_id=r.concept_id,
                concept_code=c.code if c else "",
                concept_name=c.name_en if c else "",
                grade=c.grade if c else student.grade,
                p_know=r.p_know,
                level_name=evaluate_mastery_level(r.p_know),
                total_attempts=r.total_attempts,
                total_correct=r.total_correct,
                last_assessed_at=r.last_assessed_at,
            )
        )
    return items


@router.get(
    "/{student_id}/concepts/{concept_id}/chain",
    response_model=ConceptChainResponse,
)
async def get_student_concept_chain(
    student_id: str,
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    # Fetch target concept
    c_stmt = select(Concept).where(Concept.id == concept_id)
    c_res = await db.execute(c_stmt)
    target_concept = c_res.scalar_one_or_none()
    if not target_concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id '{concept_id}' not found",
        )

    chain_data = await get_prerequisite_chain(db, concept_id)

    # Get student masteries for these concepts
    concept_ids = [c["id"] for c in chain_data]
    m_stmt = select(StudentMastery).where(
        StudentMastery.student_id == student.id,
        StudentMastery.concept_id.in_(concept_ids),
    )
    m_res = await db.execute(m_stmt)
    mastery_map = {m.concept_id: m for m in m_res.scalars().all()}

    nodes = []
    for c in chain_data:
        m = mastery_map.get(c["id"])
        p_know = m.p_know if m else 0.0
        nodes.append(
            ConceptChainNode(
                id=c["id"],
                code=c["code"],
                name_en=c["name_en"],
                grade=c["grade"],
                p_know=p_know,
                level_name=evaluate_mastery_level(p_know),
                is_mastered=(p_know >= 0.85),
            )
        )

    return ConceptChainResponse(
        target_concept_id=target_concept.id,
        target_concept_name=target_concept.name_en,
        chain=nodes,
    )


# ─── LEARN MODULE ENDPOINTS ───────────────────────────────────────────────────

@router.get("/{student_id}/learn/active", response_model=ActiveLessonResponse)
async def get_active_lesson(
    student_id: str,
    concept_id: Optional[str] = Query(None, description="Optional specific concept ID to review"),
    lang: str = Query("en", description="Language preference: en, te, hi"),
    subject_id: Optional[str] = Query(None, description="Restrict recommendations to this subject"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    if concept_id:
        c_stmt = select(Concept).where(Concept.id == concept_id)
        c_res = await db.execute(c_stmt)
        active_concept = c_res.scalar_one_or_none()
        if not active_concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept with id '{concept_id}' not found",
            )
        m_stmt = (
            select(StudentMastery)
            .where(StudentMastery.student_id == student.id, StudentMastery.concept_id == concept_id)
            .options(selectinload(StudentMastery.working_concept))
        )
        m_res = await db.execute(m_stmt)
        sm = m_res.scalar_one_or_none()
        working_concept = sm.working_concept if sm and sm.working_concept else active_concept
        is_foundation = working_concept.id != active_concept.id
    else:
        # Subject-aware selection: never leave the selected subject.
        m_stmt = (
            select(StudentMastery)
            .join(Concept, StudentMastery.concept_id == Concept.id)
            .where(StudentMastery.student_id == student.id)
            .options(selectinload(StudentMastery.concept), selectinload(StudentMastery.working_concept))
            .order_by(StudentMastery.p_know.asc())
        )
        if subject_id:
            m_stmt = (
                m_stmt.join(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
                .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
                .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
                .where(CurriculumUnit.subject_id == subject_id)
            )
        masteries = (await db.execute(m_stmt)).scalars().all()
        chosen_mastery = next((m for m in masteries if m.concept and m.p_know < 0.85), masteries[0] if masteries else None)
        if chosen_mastery and chosen_mastery.concept:
            active_concept = chosen_mastery.concept
            working_concept = chosen_mastery.working_concept or active_concept
            is_foundation = working_concept.id != active_concept.id
        else:
            active_concept = await _next_concept_in_subject(db, student.id, subject_id)
            if not active_concept:
                raise HTTPException(status_code=404, detail="No concepts available for this subject yet")
            working_concept = active_concept
            is_foundation = False

    c_name = (
        (active_concept.name_te if lang == "te" and active_concept.name_te else None)
        or (active_concept.name_hi if lang == "hi" and active_concept.name_hi else None)
        or active_concept.name_en
    )

    w_name = (
        (working_concept.name_te if lang == "te" and working_concept.name_te else None)
        or (working_concept.name_hi if lang == "hi" and working_concept.name_hi else None)
        or working_concept.name_en
    )

    # 1) Approved stored lesson (translated + cached) 2) legacy hand-written lessons 3) explicit "pending"
    stored = await lesson_service.get_approved_lesson(db, working_concept.id)
    subj_row = (await db.execute(
        select(CurriculumSubject.id, CurriculumSubject.name_en, CurriculumSubject.name_te, CurriculumSubject.name_hi)
        .join(CurriculumUnit, CurriculumUnit.subject_id == CurriculumSubject.id)
        .join(CurriculumChapter, CurriculumChapter.unit_id == CurriculumUnit.id)
        .join(CurriculumTopic, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .where(CurriculumTopic.id == working_concept.topic_id))).first()
    resp_subject_id = subj_row[0] if subj_row else None
    subject_name = (subj_row[2] if lang == "te" and subj_row and subj_row[2] else None) or \
                   (subj_row[3] if lang == "hi" and subj_row and subj_row[3] else None) or (subj_row[1] if subj_row else "General")
    extra, lesson_source, served_lang, fallback = None, "legacy", "en", False
    if stored:
        content, served_lang, fallback = await lesson_service.get_lesson_for_language(db, stored, lang, working_concept.grade)
        lesson_source = "stored"
        titles = {"simple": "Simple", "detailed": "Detailed", "visual": "Visual", "analogy": "Real-world Analogy", "worked": "Worked Example"}
        styles = {("worked_example" if k == "worked" else k): ExplanationStyleItem(title=titles[k], content=content["styles"][k]) for k in titles}
        key_terms = content.get("key_terms", [])
        cc = content["comprehension"]
        comp_q, options, correct_idx, explanation = cc["question"], cc["options"], cc["correct_index"], cc["explanation"]
        extra = {k: content.get(k) for k in ("introduction", "objectives", "definitions", "formulas", "misconceptions", "summary")}
    elif working_concept.code.startswith("NC"):
        lesson_source = "legacy"
        _, key_terms, raw_styles, fallback_comp = get_concept_lesson_content(
            concept_code=working_concept.code, concept_name=working_concept.name_en,
            grade=working_concept.grade, subject_domain=subject_name.lower(), lang=lang)
        styles = {k: ExplanationStyleItem(title=v["title"], content=v["content"]) for k, v in raw_styles.items()}
        q_item = (await db.execute(select(Question).where(Question.concept_id == working_concept.id, Question.approval_status == "approved").limit(1))).scalar_one_or_none()
        if q_item:
            comp_q = (q_item.body_te.get("text") if lang == "te" and q_item.body_te else None) or \
                     (q_item.body_hi.get("text") if lang == "hi" and q_item.body_hi else None) or q_item.body_en.get("text", "Check comprehension")
            options = q_item.answer_data.get("options", ["Option A", "Option B", "Option C", "Option D"])
            correct_idx = q_item.answer_data.get("correct_index", 0)
            explanation = q_item.explanation_en or "Review the fundamental definitions above."
        else:
            comp_q, options = fallback_comp["question"], fallback_comp["options"]
            correct_idx, explanation = fallback_comp["correct_index"], fallback_comp["explanation"]
        extra = {
            "introduction": f"Comprehensive overview of {working_concept.name_en} according to the verified CBSE Class {working_concept.grade} curriculum.",
            "objectives": working_concept.learning_objectives or [f"Understand {working_concept.name_en}", "Apply principles to solve problems"],
            "summary": f"Key learning takeaways for {working_concept.name_en}.",
        }
    else:
        _, key_terms, raw_styles, fallback_comp = get_concept_lesson_content(
            concept_code=working_concept.code, concept_name=working_concept.name_en,
            grade=working_concept.grade, subject_domain="general", lang=lang)
        styles = {k: ExplanationStyleItem(title=v["title"], content=v["content"]) for k, v in raw_styles.items()}
        q_item = (await db.execute(select(Question).where(Question.concept_id == working_concept.id, Question.approval_status == "approved").limit(1))).scalar_one_or_none()
        if q_item:
            comp_q = (q_item.body_te.get("text") if lang == "te" and q_item.body_te else None) or \
                     (q_item.body_hi.get("text") if lang == "hi" and q_item.body_hi else None) or q_item.body_en.get("text", "Check comprehension")
            options = q_item.answer_data.get("options", ["Option A", "Option B", "Option C", "Option D"])
            correct_idx = q_item.answer_data.get("correct_index", 0)
            explanation = q_item.explanation_en or "Review the fundamental definitions above."
        else:
            comp_q, options = fallback_comp["question"], fallback_comp["options"]
            correct_idx, explanation = fallback_comp["correct_index"], fallback_comp["explanation"]

    # Prereqs and related concepts
    from app.services.curriculum import get_immediate_prerequisites
    prereq_rows = await get_immediate_prerequisites(db, working_concept.id)
    prereq_list = [
        {
            "id": p.get("prerequisite_id", ""),
            "code": p.get("code", ""),
            "name": p.get("name_en", ""),
            "grade": p.get("grade", 9),
            "is_strict": p.get("is_strict", True),
        }
        for p in prereq_rows
    ]

    sib_stmt = select(Concept).where(
        Concept.topic_id == working_concept.topic_id,
        Concept.id != working_concept.id,
        Concept.is_active.is_(True),
    ).limit(5)
    siblings = (await db.execute(sib_stmt)).scalars().all()
    related_list = [
        {"id": sib.id, "name": sib.name_en, "difficulty": sib.difficulty_band, "grade": sib.grade}
        for sib in siblings
    ]

    return ActiveLessonResponse(
        concept_id=active_concept.id,
        concept_name=c_name,
        grade=working_concept.grade,
        subject_name=subject_name,
        subject_id=resp_subject_id,
        working_level_name=w_name if is_foundation else None,
        is_foundation_path=is_foundation,
        key_terms=key_terms,
        styles=styles,
        comprehension_check=ComprehensionCheckItem(question=comp_q, options=options, correct_index=correct_idx, explanation=explanation),
        lesson_source=lesson_source,
        language_served=served_lang,
        translation_fallback=fallback,
        extra=extra,
        prerequisites=prereq_list,
        related_concepts=related_list,
    )


async def _next_concept_in_subject(db: AsyncSession, student_pk: str, subject_id: Optional[str]) -> Optional[Concept]:
    """First concept of the subject whose strict prerequisites are mastered (or absent)."""
    q = (select(Concept).join(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
         .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
         .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
         .where(Concept.is_active.is_(True)).order_by(Concept.grade, Concept.sort_order))
    if subject_id:
        q = q.where(CurriculumUnit.subject_id == subject_id)
    concepts = (await db.execute(q)).scalars().all()
    mastery = {m.concept_id: m.p_know for m in (await db.execute(select(StudentMastery).where(StudentMastery.student_id == student_pk))).scalars().all()}
    prereqs: dict = {}
    for pr in (await db.execute(select(ConceptPrerequisite).where(ConceptPrerequisite.is_strict.is_(True)))).scalars().all():
        prereqs.setdefault(pr.concept_id, []).append(pr.prerequisite_id)
    for c in concepts:
        if mastery.get(c.id, 0) >= 0.85:
            continue
        if all(mastery.get(p, 0) >= 0.6 for p in prereqs.get(c.id, [])):
            return c
    return concepts[0] if concepts else None


@router.get("/{student_id}/subjects/progress")
async def get_subject_progress(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    """Per-subject progress computed from real concepts and mastery rows (no placeholders)."""
    student = await _resolve_student_profile(db, student_id)
    rows = (await db.execute(
        select(CurriculumSubject.id, CurriculumSubject.name_en, CurriculumSubject.name_te, CurriculumSubject.name_hi,
               Concept.id, CurriculumChapter.id, StudentMastery.p_know, StudentMastery.total_attempts)
        .select_from(Concept)
        .join(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
        .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .join(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .outerjoin(StudentMastery, (StudentMastery.concept_id == Concept.id) & (StudentMastery.student_id == student.id))
        .where(Concept.is_active.is_(True)))).all()
    agg: dict = {}
    for sid, en, te, hi, cid, chid, p, att in rows:
        a = agg.setdefault(sid, {"subject_id": sid, "name_en": en, "name_te": te, "name_hi": hi, "concepts": 0, "studied": 0,
                                 "mastered": 0, "needs_improvement": 0, "chapters": {}})
        a["concepts"] += 1
        ch = a["chapters"].setdefault(chid, [0, 0])
        ch[0] += 1
        if att:
            a["studied"] += 1
            if p is not None and p >= 0.85:
                a["mastered"] += 1; ch[1] += 1
            elif p is not None and p < 0.5:
                a["needs_improvement"] += 1
    out = []
    for a in agg.values():
        chs = a.pop("chapters")
        a["chapters_total"] = len(chs)
        a["chapters_completed"] = sum(1 for t, m in chs.values() if t and m == t)
        a["progress_pct"] = round(100 * a["mastered"] / a["concepts"], 1) if a["concepts"] else 0
        out.append(a)
    return sorted(out, key=lambda x: x["name_en"])


# ─── SOLVE MODULE ENDPOINTS ───────────────────────────────────────────────────

@router.get("/{student_id}/solve/next", response_model=PracticeNextResponse)
async def get_practice_next_question(
    student_id: str,
    concept_id: Optional[str] = Query(None, description="Optional target concept ID to practice"),
    lang: str = Query("en", description="Language: en, te, hi"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    target_cid = concept_id
    if not target_cid:
        # Select working concept for student
        m_stmt = (
            select(StudentMastery)
            .where(StudentMastery.student_id == student.id)
            .options(selectinload(StudentMastery.concept), selectinload(StudentMastery.working_concept))
            .order_by(StudentMastery.p_know.asc())
        )
        m_res = await db.execute(m_stmt)
        masteries = m_res.scalars().all()

        active_mastery = masteries[0] if masteries else None
        target_cid = (
            active_mastery.working_concept_id or active_mastery.concept_id
            if active_mastery
            else None
        )

    # Fetch approved questions for this concept
    q_stmt = select(Question).where(Question.approval_status == "approved")
    if target_cid:
        q_stmt = q_stmt.where(Question.concept_id == target_cid)
    q_stmt = q_stmt.order_by(Question.created_at.desc()).limit(15)

    q_res = await db.execute(q_stmt)
    questions = q_res.scalars().all()

    if not questions:
        # Fallback to any approved question
        fb_stmt = select(Question).where(Question.approval_status == "approved").limit(10)
        fb_res = await db.execute(fb_stmt)
        questions = fb_res.scalars().all()

    chosen_q = random.choice(questions)

    # Concept name
    c_stmt = select(Concept).where(Concept.id == chosen_q.concept_id)
    c_res = await db.execute(c_stmt)
    concept = c_res.scalar_one_or_none()
    concept_name = (
        (concept.name_te if lang == "te" and concept.name_te else None)
        or (concept.name_hi if lang == "hi" and concept.name_hi else None)
        or (concept.name_en if concept else "Concept Practice")
    )

    q_body = (
        (chosen_q.body_te.get("text") if lang == "te" and chosen_q.body_te else None)
        or (chosen_q.body_hi.get("text") if lang == "hi" and chosen_q.body_hi else None)
        or (chosen_q.body_en.get("text", "") if chosen_q.body_en else "")
    )

    diff_label = "easy" if chosen_q.difficulty < 0.4 else "medium" if chosen_q.difficulty <= 0.7 else "hard"

    hints = chosen_q.hints
    if not hints:
        q_text = chosen_q.body_en.get("text", "") if chosen_q.body_en else ""
        c_code = concept.code if concept else ""
        hints = get_concept_hints(concept_code=c_code, question_text=q_text)

    return PracticeNextResponse(
        question=PracticeQuestionDTO(
            id=chosen_q.id,
            concept_id=chosen_q.concept_id,
            concept_name=concept_name,
            difficulty=chosen_q.difficulty,
            difficulty_label=diff_label,
            body=q_body,
            options=chosen_q.answer_data.get("options", []),
            hints=hints,
        ),
        streak=student.current_streak,
        xp=student.total_xp,
    )


@router.post("/{student_id}/solve/submit", response_model=PracticeSubmitResponse)
async def submit_practice_answer(
    student_id: str,
    req: PracticeSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    q_stmt = select(Question).where(Question.id == req.question_id)
    q_res = await db.execute(q_stmt)
    question = q_res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    correct_idx = question.answer_data.get("correct_index", 0)
    is_correct = (req.selected_option == correct_idx)

    # Fetch student mastery for this concept
    m_stmt = select(StudentMastery).where(
        StudentMastery.student_id == student.id,
        StudentMastery.concept_id == question.concept_id,
    )
    m_res = await db.execute(m_stmt)
    mastery = m_res.scalar_one_or_none()

    if not mastery:
        mastery = StudentMastery(
            student_id=student.id,
            concept_id=question.concept_id,
            p_know=0.20,
            p_learn=0.20,
            p_guess=0.20,
            p_slip=0.10,
            working_concept_id=question.concept_id,
            total_attempts=0,
            total_correct=0,
        )
        db.add(mastery)

    prior_p = mastery.p_know or 0.20
    new_p = update_bkt(
        p_know=prior_p,
        is_correct=is_correct,
        p_learn=mastery.p_learn or 0.20,
        p_guess=mastery.p_guess or 0.20,
        p_slip=mastery.p_slip or 0.10,
    )

    mastery.p_know = new_p
    mastery.total_attempts += 1
    if is_correct:
        mastery.total_correct += 1
        mastery.consecutive_high += 1
        mastery.consecutive_low = 0
        student.total_xp += 10
        student.current_streak += 1
        if student.current_streak > student.longest_streak:
            student.longest_streak = student.current_streak
    else:
        mastery.consecutive_low += 1
        mastery.consecutive_high = 0

    now = datetime.now(timezone.utc)
    mastery.last_assessed_at = now
    student.last_active_at = now

    # Record history
    history = MasteryHistory(
        mastery_id=mastery.id,
        student_id=student.id,
        concept_id=question.concept_id,
        p_know_before=prior_p,
        p_know_after=new_p,
        trigger_event="solve_practice",
        answer_correct=is_correct,
        error_type=question.primary_error_type if not is_correct else None,
    )
    db.add(history)
    await db.commit()

    return PracticeSubmitResponse(
        is_correct=is_correct,
        correct_index=correct_idx,
        explanation=question.explanation_en or "The correct answer follows directly from first principles.",
        error_type=question.primary_error_type if not is_correct else None,
        new_p_know=new_p,
        earned_xp=student.total_xp,
        current_streak=student.current_streak,
    )


# ─── TEST MODULE ENDPOINTS ────────────────────────────────────────────────────

@router.get("/{student_id}/test/active", response_model=ActiveTestResponse)
async def get_active_test_paper(
    student_id: str,
    lang: str = Query("en", description="Language: en, te, hi"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    # Blueprint: 60% Working Level, 25% Prerequisite Probes, 15% Stretch
    # Fetch questions
    q_stmt = (
        select(Question)
        .where(Question.approval_status == "approved")
        .options(selectinload(Question.concept))
        .limit(30)
    )
    q_res = await db.execute(q_stmt)
    all_qs = q_res.scalars().all()

    if not all_qs:
        raise HTTPException(status_code=404, detail="No approved questions available")

    # Select 10 questions with section types
    sample_size = min(len(all_qs), 10)
    chosen_qs = random.sample(all_qs, sample_size)

    items = []
    for idx, q in enumerate(chosen_qs):
        sec_type = "working_level" if idx < 6 else "prereq_probe" if idx < 8 else "stretch"
        c_name = (
            (q.concept.name_te if lang == "te" and q.concept.name_te else None)
            or (q.concept.name_hi if lang == "hi" and q.concept.name_hi else None)
            or (q.concept.name_en if q.concept else "Assessment Concept")
        )
        q_text = (
            (q.body_te.get("text") if lang == "te" and q.body_te else None)
            or (q.body_hi.get("text") if lang == "hi" and q.body_hi else None)
            or q.body_en.get("text", "")
        )

        items.append(
            TestItemDTO(
                question_id=q.id,
                concept_id=q.concept_id,
                concept_name=c_name,
                section_type=sec_type,
                question_text=q_text,
                options=q.answer_data.get("options", []),
            )
        )

    return ActiveTestResponse(
        assessment_id="weekly_adaptive_quest",
        title="Weekly Adaptive Quest (60/25/15 Blueprint)",
        time_limit_mins=30,
        total_questions=len(items),
        items=items,
    )


@router.post("/{student_id}/test/submit", response_model=TestSubmitResultResponse)
async def submit_test_paper(
    student_id: str,
    req: TestSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    total = len(req.responses)
    correct_count = 0
    now = datetime.now(timezone.utc)
    proposal_generated = False
    prereq_diagnosed_name = None

    # Ensure Assessment record exists in DB
    assess_id = req.assessment_id or "weekly_adaptive_quest"
    a_stmt = select(Assessment).where(Assessment.id == assess_id)
    assessment = (await db.execute(a_stmt)).scalar_one_or_none()
    if not assessment:
        assessment = Assessment(
            id=assess_id,
            title="Weekly Adaptive Quest (60/25/15 Blueprint)",
            assessment_type="weekly",
            total_marks=float(total),
            time_limit_mins=30,
            is_active=True,
        )
        db.add(assessment)
        await db.flush()

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        student_id=student.id,
        status="completed",
        score=float(correct_count),
        max_score=float(total),
        started_at=now,
        completed_at=now,
    )
    db.add(attempt)
    await db.flush()

    for item in req.responses:
        q_stmt = (
            select(Question)
            .where(Question.id == item.question_id)
            .options(selectinload(Question.concept))
        )
        q_res = await db.execute(q_stmt)
        q = q_res.scalar_one_or_none()
        if not q:
            continue

        is_correct = (item.selected_option == q.answer_data.get("correct_index", 0))
        if is_correct:
            correct_count += 1

        # Record individual attempt response
        attempt_resp = AttemptResponse(
            attempt_id=attempt.id,
            question_id=q.id,
            student_response={"selected_option": item.selected_option},
            is_correct=is_correct,
            points_awarded=1.0 if is_correct else 0.0,
        )
        db.add(attempt_resp)

        # BKT Update for this concept
        m_stmt = select(StudentMastery).where(
            StudentMastery.student_id == student.id,
            StudentMastery.concept_id == q.concept_id,
        )
        m_res = await db.execute(m_stmt)
        mastery = m_res.scalar_one_or_none()

        if not mastery:
            mastery = StudentMastery(
                student_id=student.id,
                concept_id=q.concept_id,
                p_know=0.20,
                p_learn=0.20,
                p_guess=0.20,
                p_slip=0.10,
                working_concept_id=q.concept_id,
                total_attempts=0,
                total_correct=0,
                consecutive_high=0,
                consecutive_low=0,
            )
            db.add(mastery)

        prior_p = mastery.p_know or 0.20
        new_p = update_bkt(
            p_know=prior_p,
            is_correct=is_correct,
            p_learn=mastery.p_learn or 0.20,
            p_guess=mastery.p_guess or 0.20,
            p_slip=mastery.p_slip or 0.10,
        )
        mastery.p_know = new_p
        mastery.total_attempts = (mastery.total_attempts or 0) + 1
        if is_correct:
            mastery.total_correct = (mastery.total_correct or 0) + 1
            mastery.consecutive_high = (mastery.consecutive_high or 0) + 1
            mastery.consecutive_low = 0
        else:
            mastery.consecutive_low = (mastery.consecutive_low or 0) + 1
            mastery.consecutive_high = 0

            # Two-Consistent-Results Rule Check:
            # If 2 consecutive poor results on working level with prerequisite error,
            # trigger backward diagnosis and proposal
            if mastery.consecutive_low >= 2 and not is_correct and not proposal_generated:
                prereqs = await get_prerequisite_chain(db, q.concept_id)
                # Find earliest prerequisite gap
                if len(prereqs) > 1:
                    root_prereq = prereqs[0]  # Foundational root ancestor
                    prereq_diagnosed_name = root_prereq["name_en"]

                    proposal = LevelChangeProposal(
                        student_id=student.id,
                        target_concept_id=q.concept_id,
                        proposed_level_concept_id=root_prereq["id"],
                        proposal_type="remediation",
                        evidence={
                            "recent_scores": [round(correct_count / max(total, 1), 2)],
                            "consecutive_failures": mastery.consecutive_low,
                            "diagnosed_root_gap": root_prereq["name_en"],
                            "grade_origin": root_prereq["grade"],
                        },
                        narrative_en=(
                            f"Student {student.user.name or 'Student'} registered 2 consecutive low test scores on {q.concept.name_en}. "
                            f"Diagnostic engine traced root prerequisite gap to Class {root_prereq['grade']}: {root_prereq['name_en']}. "
                            f"Recommended Foundation Path."
                        ),
                        status="pending",
                    )
                    db.add(proposal)
                    proposal_generated = True

    accuracy = round((correct_count / max(total, 1)) * 100)
    student.total_xp += correct_count * 10
    student.last_active_at = now
    await db.commit()

    feedback = (
        f"You scored {correct_count} out of {total} ({accuracy}%). "
        + ("Excellent concept mastery demonstrated!" if accuracy >= 80 else "Practice and micro-lessons are ready to support your growth path.")
    )

    return TestSubmitResultResponse(
        attempt_id=attempt.id,
        score=correct_count,
        max_score=total,
        accuracy_pct=accuracy,
        feedback_message=feedback,
        prerequisite_diagnosed=prereq_diagnosed_name,
        proposal_sent_to_teacher=proposal_generated,
    )


@router.get("/{student_id}/test/list", response_model=TestListResponse)
async def list_student_tests(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    # 1. Available active tests
    active_tests = [
        TestOverviewItem(
            id="weekly_adaptive_quest",
            title="Weekly Adaptive Quest (60/25/15 Blueprint)",
            assessment_type="adaptive_weekly",
            time_limit_mins=30,
            total_questions=10,
            subjects_covered=["Science", "Mathematics", "English"],
            status="available",
        ),
        TestOverviewItem(
            id="cbse_diagnostic_checkpoint",
            title="CBSE Term 1 Diagnostic Mastery Assessment",
            assessment_type="diagnostic",
            time_limit_mins=45,
            total_questions=15,
            subjects_covered=["Science", "Mathematics"],
            status="available",
        ),
    ]

    # 2. Upcoming scheduled tests
    upcoming_tests = [
        TestOverviewItem(
            id="national_science_quest",
            title="National Science & Mathematics Olympiad Qualifier",
            assessment_type="olympiad",
            time_limit_mins=60,
            total_questions=25,
            subjects_covered=["Science", "Mathematics", "Computer Science"],
            status="upcoming",
            scheduled_for=datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc),
        ),
    ]

    # 3. Past completed attempts
    att_stmt = (
        select(AssessmentAttempt, Assessment)
        .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
        .where(
            AssessmentAttempt.student_id == student.id,
            Assessment.assessment_type.in_(["weekly", "adaptive_weekly", "diagnostic"]),
        )
        .order_by(AssessmentAttempt.started_at.desc())
        .limit(20)
    )
    att_rows = (await db.execute(att_stmt)).all()

    history = []
    for att, assess in att_rows:
        score = att.score or 0.0
        max_score = att.max_score or 1.0
        pct = round((score / max(max_score, 1.0)) * 100)
        history.append(
            TestHistoryItem(
                attempt_id=att.id,
                assessment_id=assess.id,
                title=assess.title,
                score=score,
                max_score=max_score,
                accuracy_pct=pct,
                started_at=att.started_at,
                completed_at=att.completed_at,
                status=att.status,
            )
        )

    return TestListResponse(
        available=active_tests,
        upcoming=upcoming_tests,
        history=history,
    )


@router.get("/{student_id}/test/attempts/{attempt_id}", response_model=TestAttemptReviewResponse)
async def get_test_attempt_review(
    student_id: str,
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    att_stmt = (
        select(AssessmentAttempt, Assessment)
        .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
        .where(AssessmentAttempt.id == attempt_id, AssessmentAttempt.student_id == student.id)
    )
    att_row = (await db.execute(att_stmt)).first()
    if not att_row:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    attempt, assessment = att_row

    # Responses
    resp_stmt = (
        select(AttemptResponse, Question, Concept)
        .join(Question, AttemptResponse.question_id == Question.id)
        .outerjoin(Concept, Question.concept_id == Concept.id)
        .where(AttemptResponse.attempt_id == attempt.id)
        .order_by(AttemptResponse.created_at.asc())
    )
    resp_rows = (await db.execute(resp_stmt)).all()

    questions_review = []
    for resp, q, c in resp_rows:
        sel_opt = resp.student_response.get("selected_option") if resp.student_response else None
        corr_opt = q.answer_data.get("correct_index", 0)
        questions_review.append(
            TestQuestionReviewItem(
                question_id=q.id,
                concept_id=q.concept_id,
                concept_name=c.name_en if c else "Concept Review",
                section_type=q.bloom_level or "working_level",
                question_text=q.body_en.get("text", "") if q.body_en else "",
                options=q.answer_data.get("options", []),
                selected_option=sel_opt,
                correct_option=corr_opt,
                is_correct=resp.is_correct,
                explanation=q.explanation_en or "Derived directly from first principles.",
            )
        )

    score = attempt.score or 0.0
    max_score = attempt.max_score or float(len(questions_review))
    pct = round((score / max(max_score, 1.0)) * 100)

    time_mins = 0
    if attempt.completed_at and attempt.started_at:
        time_mins = max(1, int((attempt.completed_at - attempt.started_at).total_seconds() / 60))

    return TestAttemptReviewResponse(
        attempt_id=attempt.id,
        assessment_id=assessment.id,
        title=assessment.title,
        score=score,
        max_score=max_score,
        accuracy_pct=pct,
        time_taken_mins=time_mins,
        completed_at=attempt.completed_at or attempt.started_at,
        questions=questions_review,
    )


# ─── TOPIC-WISE INDEPENDENT PRACTICE MODULE ───────────────────────────────────

@router.get("/{student_id}/practice/filters", response_model=PracticeFilterOptionsResponse)
async def get_practice_filters(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    # Fetch subjects, units, chapters, topics
    subjs = (await db.execute(select(CurriculumSubject).where(CurriculumSubject.is_active.is_(True)).order_by(CurriculumSubject.sort_order))).scalars().all()
    units = (await db.execute(select(CurriculumUnit).order_by(CurriculumUnit.grade, CurriculumUnit.unit_no))).scalars().all()
    chaps = (await db.execute(select(CurriculumChapter).order_by(CurriculumChapter.chapter_no))).scalars().all()
    topics = (await db.execute(select(CurriculumTopic).order_by(CurriculumTopic.topic_no))).scalars().all()

    topics_by_chap: dict = {}
    for t in topics:
        topics_by_chap.setdefault(t.chapter_id, []).append(
            FilterTopicItem(id=t.id, topic_no=t.topic_no, name=t.name_en)
        )

    chaps_by_unit: dict = {}
    for ch in chaps:
        chaps_by_unit.setdefault(ch.unit_id, []).append(
            FilterChapterItem(
                id=ch.id,
                chapter_no=ch.chapter_no,
                name=ch.name_en,
                topics=topics_by_chap.get(ch.id, []),
            )
        )

    # Group by grade
    grades_map: dict = {}
    for u in units:
        subj = next((s for s in subjs if s.id == u.subject_id), None)
        if not subj:
            continue
        g_subj_list = grades_map.setdefault(u.grade, {})
        subj_entry = g_subj_list.setdefault(
            subj.id,
            FilterSubjectItem(
                id=subj.id,
                code=subj.code,
                name=subj.name_en,
                domain=subj.domain,
                chapters=[],
            ),
        )
        subj_entry.chapters.extend(chaps_by_unit.get(u.id, []))

    grade_items = []
    for g, s_dict in sorted(grades_map.items()):
        grade_items.append(FilterGradeItem(grade=g, subjects=list(s_dict.values())))

    return PracticeFilterOptionsResponse(grades=grade_items)


@router.post("/{student_id}/practice/session", response_model=PracticeSessionResponse)
async def create_practice_session(
    student_id: str,
    req: PracticeSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    lang = req.lang

    # Build question query with hierarchy joins
    q_stmt = (
        select(Question, Concept)
        .join(Concept, Question.concept_id == Concept.id)
        .outerjoin(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
        .outerjoin(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .outerjoin(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .where(Question.approval_status == "approved")
    )

    if req.concept_id:
        q_stmt = q_stmt.where(Question.concept_id == req.concept_id)
    elif req.topic_id:
        q_stmt = q_stmt.where(Concept.topic_id == req.topic_id)
    elif req.chapter_id:
        q_stmt = q_stmt.where(CurriculumTopic.chapter_id == req.chapter_id)
    elif req.subject_id:
        q_stmt = q_stmt.where(CurriculumUnit.subject_id == req.subject_id)
    elif req.grade:
        q_stmt = q_stmt.where(Concept.grade == req.grade)

    if req.difficulty and req.difficulty != "all":
        if req.difficulty == "easy":
            q_stmt = q_stmt.where(Question.difficulty < 0.45)
        elif req.difficulty == "medium":
            q_stmt = q_stmt.where(Question.difficulty >= 0.45, Question.difficulty < 0.75)
        elif req.difficulty == "hard":
            q_stmt = q_stmt.where(Question.difficulty >= 0.75)

    q_stmt = q_stmt.limit(50)
    q_rows = (await db.execute(q_stmt)).all()

    # Fallback to any approved questions if specific filter has insufficient pool
    if len(q_rows) < req.count:
        fb_stmt = select(Question, Concept).join(Concept, Question.concept_id == Concept.id).where(Question.approval_status == "approved").limit(30)
        fb_rows = (await db.execute(fb_stmt)).all()
        # combine without duplicates
        seen = {q.id for q, _ in q_rows}
        for q, c in fb_rows:
            if q.id not in seen:
                q_rows.append((q, c))
                seen.add(q.id)

    # Randomly select requested count
    chosen_rows = random.sample(q_rows, min(len(q_rows), max(1, req.count)))

    questions_dto = []
    for q, c in chosen_rows:
        c_name = (
            (c.name_te if lang == "te" and c.name_te else None)
            or (c.name_hi if lang == "hi" and c.name_hi else None)
            or c.name_en
        )
        q_body = (
            (q.body_te.get("text") if lang == "te" and q.body_te else None)
            or (q.body_hi.get("text") if lang == "hi" and q.body_hi else None)
            or (q.body_en.get("text", "") if q.body_en else "")
        )
        diff_label = "easy" if q.difficulty < 0.4 else "medium" if q.difficulty <= 0.7 else "hard"
        hints = q.hints or get_concept_hints(c.code, q_body)

        questions_dto.append(
            PracticeSessionQuestion(
                id=q.id,
                concept_id=q.concept_id,
                concept_name=c_name,
                difficulty=q.difficulty,
                difficulty_label=diff_label,
                body=q_body,
                options=q.answer_data.get("options", []),
                hints=hints,
            )
        )

    session_id = f"practice_{random.randint(100000, 999999)}"
    title = "Topic Practice Session"
    if req.concept_id and chosen_rows:
        title = f"Practice: {chosen_rows[0][1].name_en}"
    elif req.chapter_id:
        title = "Chapter Mastery Practice"

    return PracticeSessionResponse(
        session_id=session_id,
        title=title,
        total_questions=len(questions_dto),
        difficulty=req.difficulty or "all",
        questions=questions_dto,
        streak=student.current_streak,
        xp=student.total_xp,
    )


@router.post("/{student_id}/practice/session/submit", response_model=PracticeSessionSubmitResponse)
async def submit_practice_session(
    student_id: str,
    req: PracticeSessionSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    now = datetime.now(timezone.utc)

    # Create Assessment for Practice
    assess_title = "Topic Practice Session"
    a_stmt = select(Assessment).where(Assessment.title == assess_title, Assessment.assessment_type == "practice")
    assessment = (await db.execute(a_stmt)).scalar_one_or_none()
    if not assessment:
        assessment = Assessment(
            title=assess_title,
            assessment_type="practice",
            total_marks=float(len(req.responses)),
            time_limit_mins=20,
            is_active=True,
        )
        db.add(assessment)
        await db.flush()

    correct_count = 0
    total = len(req.responses)

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        student_id=student.id,
        status="completed",
        score=0.0,
        max_score=float(total),
        started_at=now,
        completed_at=now,
    )
    db.add(attempt)
    await db.flush()

    results = []
    earned_xp = 0

    for item in req.responses:
        q_stmt = select(Question, Concept).join(Concept, Question.concept_id == Concept.id).where(Question.id == item.question_id)
        q_row = (await db.execute(q_stmt)).first()
        if not q_row:
            continue
        q, c = q_row

        corr_idx = q.answer_data.get("correct_index", 0)
        is_correct = (item.selected_option == corr_idx)
        if is_correct:
            correct_count += 1
            earned_xp += 10

        # Save response record
        att_resp = AttemptResponse(
            attempt_id=attempt.id,
            question_id=q.id,
            student_response={
                "selected_option": item.selected_option,
                "hints_used": item.hints_used,
            },
            is_correct=is_correct,
            points_awarded=1.0 if is_correct else 0.0,
            time_spent_secs=item.time_spent_secs,
        )
        db.add(att_resp)

        # Update BKT
        m_stmt = select(StudentMastery).where(
            StudentMastery.student_id == student.id,
            StudentMastery.concept_id == q.concept_id,
        )
        mastery = (await db.execute(m_stmt)).scalar_one_or_none()
        if not mastery:
            mastery = StudentMastery(
                student_id=student.id,
                concept_id=q.concept_id,
                p_know=0.20,
                p_learn=0.20,
                p_guess=0.20,
                p_slip=0.10,
                working_concept_id=q.concept_id,
                total_attempts=0,
                total_correct=0,
                consecutive_high=0,
                consecutive_low=0,
            )
            db.add(mastery)

        prior_p = mastery.p_know or 0.20
        new_p = update_bkt(
            p_know=prior_p,
            is_correct=is_correct,
            p_learn=mastery.p_learn or 0.20,
            p_guess=mastery.p_guess or 0.20,
            p_slip=mastery.p_slip or 0.10,
        )
        mastery.p_know = new_p
        mastery.total_attempts = (mastery.total_attempts or 0) + 1
        if is_correct:
            mastery.total_correct = (mastery.total_correct or 0) + 1
            mastery.consecutive_high = (mastery.consecutive_high or 0) + 1
            mastery.consecutive_low = 0
        else:
            mastery.consecutive_low = (mastery.consecutive_low or 0) + 1
            mastery.consecutive_high = 0
        mastery.last_assessed_at = now

        # Add to results review
        results.append(
            PracticeQuestionReview(
                question_id=q.id,
                concept_id=q.concept_id,
                concept_name=c.name_en,
                question_text=q.body_en.get("text", "") if q.body_en else "",
                options=q.answer_data.get("options", []),
                selected_option=item.selected_option,
                correct_option=corr_idx,
                is_correct=is_correct,
                explanation=q.explanation_en or "Review the fundamental definitions above.",
            )
        )

    accuracy_pct = round((correct_count / max(total, 1)) * 100)
    attempt.score = float(correct_count)

    student.total_xp += earned_xp
    if accuracy_pct >= 60:
        student.current_streak += 1
        if student.current_streak > student.longest_streak:
            student.longest_streak = student.current_streak

    student.last_active_at = now
    await db.commit()

    return PracticeSessionSubmitResponse(
        attempt_id=attempt.id,
        score=correct_count,
        total=total,
        accuracy_pct=accuracy_pct,
        earned_xp=earned_xp,
        new_total_xp=student.total_xp,
        current_streak=student.current_streak,
        results=results,
    )


@router.get("/{student_id}/practice/history", response_model=List[PracticeHistoryItem])
async def get_practice_history(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    att_stmt = (
        select(AssessmentAttempt, Assessment)
        .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
        .where(
            AssessmentAttempt.student_id == student.id,
            Assessment.assessment_type == "practice",
        )
        .order_by(AssessmentAttempt.started_at.desc())
        .limit(20)
    )
    att_rows = (await db.execute(att_stmt)).all()

    history = []
    for att, assess in att_rows:
        score = int(att.score or 0)
        max_score = int(att.max_score or 1)
        pct = round((score / max(max_score, 1)) * 100)
        time_mins = 1
        if att.completed_at and att.started_at:
            time_mins = max(1, int((att.completed_at - att.started_at).total_seconds() / 60))
        history.append(
            PracticeHistoryItem(
                attempt_id=att.id,
                date=att.started_at,
                title=assess.title,
                score=score,
                max_score=max_score,
                accuracy_pct=pct,
                time_spent_mins=time_mins,
            )
        )
    return history


# ─── PROGRESS & PROFILE ───────────────────────────────────────────────────────

@router.get("/{student_id}/progress/summary", response_model=StudentProgressSummaryResponse)
async def get_student_progress_summary(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)

    # All concepts
    c_stmt = (
        select(Concept, CurriculumTopic, CurriculumChapter, CurriculumUnit, CurriculumSubject)
        .outerjoin(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
        .outerjoin(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .outerjoin(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .outerjoin(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id)
        .where(Concept.is_active.is_(True))
    )
    c_rows = (await db.execute(c_stmt)).all()

    # All masteries for this student
    m_stmt = select(StudentMastery).where(StudentMastery.student_id == student.id)
    mastery_map = {m.concept_id: m.p_know for m in (await db.execute(m_stmt)).scalars().all()}

    subject_data: dict = {}
    mastered_count = 0
    learning_count = 0
    needs_attention_count = 0

    for c, t, ch, u, s in c_rows:
        s_id = s.id if s else "gen"
        s_name = s.name_en if s else "General"
        s_domain = s.domain if s else "general"

        p = mastery_map.get(c.id, 0.0)
        if p >= 0.85:
            mastered_count += 1
            status = "mastered"
        elif p >= 0.40:
            learning_count += 1
            status = "learning"
        else:
            needs_attention_count += 1
            status = "needs_attention"

        sd = subject_data.setdefault(
            s_id,
            {
                "subject_id": s_id,
                "subject_name": s_name,
                "domain": s_domain,
                "total": 0,
                "mastered": 0,
                "learning": 0,
                "needs_attention": 0,
                "p_sum": 0.0,
            },
        )
        sd["total"] += 1
        sd["p_sum"] += p
        if status == "mastered":
            sd["mastered"] += 1
        elif status == "learning":
            sd["learning"] += 1
        else:
            sd["needs_attention"] += 1

    subjects = []
    for s_info in subject_data.values():
        avg = round((s_info["p_sum"] / max(s_info["total"], 1)) * 100)
        subjects.append(
            SubjectProgressItem(
                subject_id=s_info["subject_id"],
                subject_name=s_info["subject_name"],
                domain=s_info["domain"],
                total_concepts=s_info["total"],
                mastered_concepts=s_info["mastered"],
                in_progress_concepts=s_info["learning"],
                needs_attention_concepts=s_info["needs_attention"],
                avg_mastery_pct=avg,
            )
        )

    total_c = len(c_rows)
    overall_pct = round((sum(mastery_map.values()) / max(total_c, 1)) * 100)

    return StudentProgressSummaryResponse(
        total_xp=student.total_xp,
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        overall_mastery_pct=overall_pct,
        total_concepts=total_c,
        mastered_count=mastered_count,
        learning_count=learning_count,
        needs_attention_count=needs_attention_count,
        subjects=subjects,
        recent_activities=[],
    )


@router.get("/{student_id}/profile")
async def get_student_profile(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    school_name = student.school.name if student.school else "CHATUR Academy"

    return {
        "id": student.id,
        "user_id": student.user_id,
        "name": student.user.name or student.user.username,
        "username": student.user.username,
        "email": student.user.email,
        "phone": student.user.phone,
        "role": student.user.role,
        "preferred_lang": student.user.preferred_lang,
        "school_id": student.school_id,
        "school_name": school_name,
        "grade": student.grade,
        "section": student.section,
        "roll_no": student.roll_no or "01",
        "total_xp": student.total_xp,
        "current_streak": student.current_streak,
        "longest_streak": student.longest_streak,
        "last_active_at": student.last_active_at,
    }


# ─── STUDENT ACADEMIC TO-DO TASKS ─────────────────────────────────────────────

@router.get("/{student_id}/tasks", response_model=List[StudentTaskResponse])
async def get_student_tasks(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access tasks of another student")

    stmt = (
        select(StudentTask)
        .where(StudentTask.student_id == student.id)
        .order_by(StudentTask.is_completed.asc(), StudentTask.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{student_id}/tasks", response_model=StudentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_student_task(
    student_id: str,
    payload: StudentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create tasks for another student")

    task = StudentTask(
        student_id=student.id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        link_type=payload.link_type,
        link_id=payload.link_id,
        link_payload=payload.link_payload,
        due_date=payload.due_date,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{student_id}/tasks/{task_id}", response_model=StudentTaskResponse)
async def update_student_task(
    student_id: str,
    task_id: str,
    payload: StudentTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify tasks of another student")

    stmt = select(StudentTask).where(StudentTask.id == task_id, StudentTask.student_id == student.id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.due_date is not None:
        task.due_date = payload.due_date
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed
        task.completed_at = datetime.now(timezone.utc) if payload.is_completed else None

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{student_id}/tasks/{task_id}")
async def delete_student_task(
    student_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student = await _resolve_student_profile(db, student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete tasks of another student")

    stmt = select(StudentTask).where(StudentTask.id == task_id, StudentTask.student_id == student.id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted successfully", "id": task_id}



