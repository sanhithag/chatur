from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db, require_role
from app.models.assessment import LevelChangeProposal, Question, StudentMastery
from app.models.curriculum import Concept
from app.models.student import ClassSection, StudentEnrollment, StudentProfile, TeacherAssignment
from app.models.teacher import RemedialGroup, RemedialGroupMember, TeacherActivityLog
from app.models.user import UserAccount
from app.schemas.assessment import (
    ContentDecisionRequest,
    LevelProposalResponse,
    ProposalDecisionRequest,
    QuestionResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.teacher import (
    ClassSectionSummary,
    ConceptGapItem,
    HeatmapConceptItem,
    HeatmapMasteryItem,
    HeatmapStudentItem,
    RemedialGroupCreate,
    RemedialGroupResponse,
    StudentAttentionItem,
    TeacherDashboardResponse,
    TeacherHeatmapResponse,
)

router = APIRouter()


@router.get("/{teacher_id}/dashboard", response_model=TeacherDashboardResponse)
async def get_teacher_dashboard(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    # Verify teacher exists
    t_stmt = select(UserAccount).where(UserAccount.id == teacher_id)
    t_res = await db.execute(t_stmt)
    teacher = t_res.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id '{teacher_id}' not found",
        )

    # Find teacher's assigned section
    assign_stmt = (
        select(TeacherAssignment)
        .where(TeacherAssignment.teacher_user_id == teacher.id)
        .options(selectinload(TeacherAssignment.section))
    )
    assign_res = await db.execute(assign_stmt)
    assignment = assign_res.scalars().first()

    section_summary = None
    section_id = None
    if assignment and assignment.section:
        sec = assignment.section
        section_id = sec.id
        section_summary = ClassSectionSummary(
            id=sec.id,
            grade=sec.grade,
            section=sec.section,
            academic_year=sec.academic_year,
        )

    # Get student count
    if section_id:
        enroll_stmt = select(func.count(StudentEnrollment.id)).where(
            StudentEnrollment.section_id == section_id,
            StudentEnrollment.is_active.is_(True),
        )
        enroll_res = await db.execute(enroll_stmt)
        total_students = enroll_res.scalar_one() or 0
    else:
        # Fallback to all students in school
        stud_stmt = select(func.count(StudentProfile.id))
        stud_res = await db.execute(stud_stmt)
        total_students = stud_res.scalar_one() or 0

    # Pending proposals
    prop_stmt = select(func.count(LevelChangeProposal.id)).where(
        LevelChangeProposal.status == "pending"
    )
    prop_res = await db.execute(prop_stmt)
    pending_proposals = prop_res.scalar_one() or 0

    # Concepts with gaps (p_know < 0.5)
    gap_stmt = (
        select(Concept.id, Concept.name_en, func.count(StudentMastery.id).label("student_count"))
        .join(StudentMastery, StudentMastery.concept_id == Concept.id)
        .where(StudentMastery.p_know < 0.50)
        .group_by(Concept.id, Concept.name_en)
        .order_by(func.count(StudentMastery.id).desc())
        .limit(5)
    )
    gap_res = await db.execute(gap_stmt)
    concepts_with_gaps = [
        ConceptGapItem(concept_id=row[0], concept_name=row[1], student_count=row[2])
        for row in gap_res.all()
    ]

    # Students needing attention (multiple gaps)
    attn_stmt = (
        select(StudentProfile.id, UserAccount.name, func.count(StudentMastery.id).label("gap_count"))
        .join(UserAccount, StudentProfile.user_id == UserAccount.id)
        .join(StudentMastery, StudentMastery.student_id == StudentProfile.id)
        .where(StudentMastery.p_know < 0.50)
        .group_by(StudentProfile.id, UserAccount.name)
        .order_by(func.count(StudentMastery.id).desc())
        .limit(5)
    )
    attn_res = await db.execute(attn_stmt)
    students_needing_attention = [
        StudentAttentionItem(student_id=row[0], student_name=row[1] or "Student", gap_count=row[2])
        for row in attn_res.all()
    ]

    return TeacherDashboardResponse(
        section=section_summary,
        total_students=total_students,
        pending_proposals=pending_proposals,
        concepts_with_gaps=concepts_with_gaps,
        students_needing_attention=students_needing_attention,
    )


@router.get("/{teacher_id}/heatmap", response_model=TeacherHeatmapResponse)
async def get_teacher_heatmap(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    # Fetch all active concepts in curriculum
    c_stmt = (
        select(Concept)
        .where(Concept.is_active.is_(True))
        .order_by(Concept.grade, Concept.sort_order)
    )
    c_res = await db.execute(c_stmt)
    concepts = c_res.scalars().all()

    concept_items = [
        HeatmapConceptItem(
            id=c.id,
            code=c.code,
            name_en=c.name_en,
            grade=c.grade,
        )
        for c in concepts
    ]

    # Fetch all students with their masteries
    stmt = (
        select(StudentProfile)
        .options(
            selectinload(StudentProfile.user),
            selectinload(StudentProfile.masteries),
        )
        .order_by(StudentProfile.roll_no)
    )
    res = await db.execute(stmt)
    students = res.scalars().all()

    student_items = []
    for s in students:
        s_name = s.user.name or s.user.username if s.user else "Student"
        mastery_list = [
            HeatmapMasteryItem(concept_id=m.concept_id, p_know=m.p_know)
            for m in s.masteries
        ]
        student_items.append(
            HeatmapStudentItem(
                student_id=s.id,
                student_name=s_name,
                grade=s.grade,
                section=s.section,
                mastery=mastery_list,
                concept_mastery=mastery_list,
            )
        )

    return TeacherHeatmapResponse(
        concepts=concept_items,
        students=student_items,
    )


@router.get("/{teacher_id}/review-queue", response_model=List[LevelProposalResponse])
async def get_review_queue(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = (
        select(LevelChangeProposal)
        .where(LevelChangeProposal.status == "pending")
        .options(
            selectinload(LevelChangeProposal.student).selectinload(StudentProfile.user),
            selectinload(LevelChangeProposal.target_concept),
            selectinload(LevelChangeProposal.proposed_level_concept),
        )
        .order_by(LevelChangeProposal.created_at.desc())
    )
    res = await db.execute(stmt)
    proposals = res.scalars().all()

    results = []
    for p in proposals:
        s_name = (
            p.student.user.name or p.student.user.username
            if p.student and p.student.user
            else "Student"
        )
        tc_name = p.target_concept.name_en if p.target_concept else "Target Concept"
        pc_name = (
            p.proposed_level_concept.name_en
            if p.proposed_level_concept
            else "Proposed Concept"
        )

        results.append(
            LevelProposalResponse(
                id=p.id,
                student_id=p.student_id,
                student_name=s_name,
                target_concept_id=p.target_concept_id,
                target_concept_name=tc_name,
                proposed_level_concept_id=p.proposed_level_concept_id,
                proposed_level_concept_name=pc_name,
                proposal_type=p.proposal_type,
                evidence=p.evidence,
                narrative_en=p.narrative_en,
                status=p.status,
                created_at=p.created_at,
            )
        )
    return results


@router.post(
    "/{teacher_id}/review-queue/{proposal_id}/decide",
    response_model=MessageResponse,
)
async def decide_proposal(
    teacher_id: str,
    proposal_id: str,
    req: ProposalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = (
        select(LevelChangeProposal)
        .where(LevelChangeProposal.id == proposal_id)
        .options(selectinload(LevelChangeProposal.student))
    )
    res = await db.execute(stmt)
    proposal = res.scalar_one_or_none()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with id '{proposal_id}' not found",
        )

    decision = req.decision.lower()
    if decision not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'approved' or 'rejected'",
        )

    now = datetime.now(timezone.utc)
    proposal.status = decision
    proposal.decided_by = teacher_id
    proposal.decided_at = now
    proposal.teacher_notes = req.teacher_notes

    # If approved, update working_concept_id in StudentMastery
    if decision == "approved":
        m_stmt = select(StudentMastery).where(
            StudentMastery.student_id == proposal.student_id,
            StudentMastery.concept_id == proposal.target_concept_id,
        )
        m_res = await db.execute(m_stmt)
        mastery = m_res.scalar_one_or_none()
        if mastery:
            mastery.working_concept_id = proposal.proposed_level_concept_id

    # Log teacher activity
    log = TeacherActivityLog(
        teacher_user_id=teacher_id,
        action=f"proposal_{decision}",
        target_type="proposal",
        target_id=proposal_id,
        metadata_json={
            "proposal_id": proposal_id,
            "decision": decision,
            "time_spent_secs": req.time_spent_secs or 0,
            "teacher_notes": req.teacher_notes,
        },
    )
    db.add(log)
    await db.commit()

    return MessageResponse(message=f"Proposal {proposal_id} {decision} successfully")


@router.get(
    "/{teacher_id}/remedial-groups",
    response_model=List[RemedialGroupResponse],
)
async def get_remedial_groups(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = (
        select(RemedialGroup)
        .where(RemedialGroup.teacher_user_id == teacher_id)
        .options(
            selectinload(RemedialGroup.concept),
            selectinload(RemedialGroup.members),
        )
        .order_by(RemedialGroup.created_at.desc())
    )
    res = await db.execute(stmt)
    groups = res.scalars().all()

    results = []
    for g in groups:
        results.append(
            RemedialGroupResponse(
                id=g.id,
                name=g.name,
                concept_id=g.concept_id,
                concept_name=g.concept.name_en if g.concept else "Concept",
                section_id=g.section_id,
                member_count=len(g.members),
                status=g.status,
                description=g.description,
                created_at=g.created_at,
            )
        )
    return results


@router.post(
    "/{teacher_id}/remedial-groups",
    response_model=RemedialGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_remedial_group(
    teacher_id: str,
    req: RemedialGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    # Verify concept exists
    c_stmt = select(Concept).where(Concept.id == req.concept_id)
    c_res = await db.execute(c_stmt)
    concept = c_res.scalar_one_or_none()
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id '{req.concept_id}' not found",
        )

    group = RemedialGroup(
        teacher_user_id=teacher_id,
        section_id=req.section_id,
        concept_id=req.concept_id,
        name=req.name,
        description=req.description,
        status="active",
    )
    db.add(group)
    await db.flush()

    for s_id in req.student_ids:
        member = RemedialGroupMember(
            group_id=group.id,
            student_id=s_id,
        )
        db.add(member)

    # Activity log
    log = TeacherActivityLog(
        teacher_user_id=teacher_id,
        action="create_remedial_group",
        target_type="remedial_group",
        target_id=group.id,
        metadata_json={
            "name": req.name,
            "concept_id": req.concept_id,
            "student_count": len(req.student_ids),
        },
    )
    db.add(log)
    await db.commit()

    return RemedialGroupResponse(
        id=group.id,
        name=group.name,
        concept_id=group.concept_id,
        concept_name=concept.name_en,
        section_id=group.section_id,
        member_count=len(req.student_ids),
        status=group.status,
        description=group.description,
        created_at=group.created_at,
    )


@router.get(
    "/{teacher_id}/content-queue",
    response_model=List[QuestionResponse],
)
async def get_content_queue(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = (
        select(Question)
        .where(Question.approval_status.in_(["pending_review", "draft"]))
        .order_by(Question.created_at.desc())
    )
    res = await db.execute(stmt)
    questions = res.scalars().all()
    return questions


@router.post(
    "/{teacher_id}/content-queue/{question_id}/decide",
    response_model=MessageResponse,
)
async def decide_content(
    teacher_id: str,
    question_id: str,
    req: ContentDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = select(Question).where(Question.id == question_id)
    res = await db.execute(stmt)
    question = res.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id '{question_id}' not found",
        )

    decision = req.decision.lower()
    if decision not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved' or 'rejected'",
        )

    question.approval_status = decision

    log = TeacherActivityLog(
        teacher_user_id=teacher_id,
        action=f"question_{decision}",
        target_type="question",
        target_id=question_id,
        metadata_json={"notes": req.notes, "decision": decision},
    )
    db.add(log)
    await db.commit()

    return MessageResponse(message=f"Question {question_id} has been {decision}")
