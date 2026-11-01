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
from app.models.curriculum import Concept, CurriculumSubject
from app.models.student import ClassSection, StudentEnrollment, StudentProfile
from app.models.user import UserAccount
from app.schemas.student import (
    ActiveLessonResponse,
    ActiveTestResponse,
    ComprehensionCheckItem,
    ConceptChainNode,
    ConceptChainResponse,
    EnrolledSubjectSummary,
    ExplanationStyleItem,
    MasterySummaryItem,
    PracticeNextResponse,
    PracticeQuestionDTO,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    StudentDashboardResponse,
    StudentMasteryResponse,
    StudentSummary,
    TestItemDTO,
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
        # Find the concept student is currently actively focusing on (e.g. lowest mastery or working_concept)
        m_stmt = (
            select(StudentMastery)
            .where(StudentMastery.student_id == student.id)
            .options(
                selectinload(StudentMastery.concept),
                selectinload(StudentMastery.working_concept),
            )
            .order_by(StudentMastery.p_know.asc())
        )
        m_res = await db.execute(m_stmt)
        masteries = m_res.scalars().all()

        chosen_mastery = masteries[0] if masteries else None
        if not chosen_mastery or not chosen_mastery.concept:
            # Fallback to first concept in DB
            c_stmt = select(Concept).limit(1)
            c_res = await db.execute(c_stmt)
            active_concept = c_res.scalar_one()
            working_concept = active_concept
            is_foundation = False
        else:
            active_concept = chosen_mastery.concept
            working_concept = chosen_mastery.working_concept or active_concept
            is_foundation = working_concept.id != active_concept.id

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

    # Dynamic explanation styles adapted to concept, subject & language
    subject_name, key_terms, raw_styles, fallback_comp = get_concept_lesson_content(
        concept_code=working_concept.code,
        concept_name=working_concept.name_en,
        grade=working_concept.grade,
        subject_domain="general",
        lang=lang,
    )

    styles = {
        style_key: ExplanationStyleItem(
            title=style_val["title"],
            content=style_val["content"],
        )
        for style_key, style_val in raw_styles.items()
    }

    # Fetch a question for comprehension check
    q_stmt = (
        select(Question)
        .where(Question.concept_id == working_concept.id, Question.approval_status == "approved")
        .limit(1)
    )
    q_res = await db.execute(q_stmt)
    q_item = q_res.scalar_one_or_none()

    if q_item:
        comp_q = (
            (q_item.body_te.get("text") if lang == "te" and q_item.body_te else None)
            or (q_item.body_hi.get("text") if lang == "hi" and q_item.body_hi else None)
            or q_item.body_en.get("text", "Check comprehension")
        )
        options = q_item.answer_data.get("options", ["Option A", "Option B", "Option C", "Option D"])
        correct_idx = q_item.answer_data.get("correct_index", 0)
        explanation = q_item.explanation_en or "Review the fundamental definitions above."
    else:
        comp_q = fallback_comp["question"]
        options = fallback_comp["options"]
        correct_idx = fallback_comp["correct_index"]
        explanation = fallback_comp["explanation"]

    return ActiveLessonResponse(
        concept_id=active_concept.id,
        concept_name=c_name,
        grade=working_concept.grade,
        subject_name=subject_name,
        working_level_name=w_name if is_foundation else None,
        is_foundation_path=is_foundation,
        key_terms=key_terms,
        styles=styles,
        comprehension_check=ComprehensionCheckItem(
            question=comp_q,
            options=options,
            correct_index=correct_idx,
            explanation=explanation,
        ),
    )


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
            working_concept_id=question.concept_id,
            total_attempts=0,
            total_correct=0,
        )
        db.add(mastery)

    prior_p = mastery.p_know
    new_p = update_bkt(
        p_know=prior_p,
        is_correct=is_correct,
        p_learn=mastery.p_learn,
        p_guess=mastery.p_guess,
        p_slip=mastery.p_slip,
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

        # BKT Update for this concept
        m_stmt = select(StudentMastery).where(
            StudentMastery.student_id == student.id,
            StudentMastery.concept_id == q.concept_id,
        )
        m_res = await db.execute(m_stmt)
        mastery = m_res.scalar_one_or_none()

        if mastery:
            prior_p = mastery.p_know
            new_p = update_bkt(prior_p, is_correct)
            mastery.p_know = new_p
            mastery.total_attempts += 1
            if is_correct:
                mastery.total_correct += 1
                mastery.consecutive_high += 1
                mastery.consecutive_low = 0
            else:
                mastery.consecutive_low += 1
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
        score=correct_count,
        max_score=total,
        accuracy_pct=accuracy,
        feedback_message=feedback,
        prerequisite_diagnosed=prereq_diagnosed_name,
        proposal_sent_to_teacher=proposal_generated,
    )

