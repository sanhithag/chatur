from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.models.assessment import StudentMastery
from app.models.curriculum import Concept, CurriculumSubject
from app.models.student import ParentChildLink, StudentProfile
from app.models.user import UserAccount
from app.services.bkt import evaluate_mastery_level

router = APIRouter()


@router.get("/{parent_id}/children")
async def get_parent_children(
    parent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    if current_user.role not in ("admin", "super_admin") and current_user.id != parent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot view another parent's children.",
        )
    stmt = (
        select(ParentChildLink)
        .where(ParentChildLink.parent_user_id == parent_id)
        .options(
            selectinload(ParentChildLink.student).selectinload(StudentProfile.user)
        )
    )
    res = await db.execute(stmt)
    links = res.scalars().all()

    children = []
    for link in links:
        stud = link.student
        if stud:
            name = stud.user.name or stud.user.username if stud.user else "Student"
            children.append({
                "student_id": stud.id,
                "user_id": stud.user_id,
                "name": name,
                "student_name": name,
                "grade": stud.grade,
                "section": stud.section,
                "roll_no": stud.roll_no,
                "relationship": link.relation_type,
                "relation_type": link.relation_type,
                "consent_given": link.consent_given,
                "total_xp": stud.total_xp,
                "current_streak": stud.current_streak,
                "longest_streak": stud.longest_streak,
            })
    return children


@router.get("/{parent_id}/children/{student_id}/progress")
async def get_child_progress(
    parent_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    if current_user.role not in ("admin", "super_admin") and current_user.id != parent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot view another parent's child data.",
        )
    # Verify link
    link_stmt = select(ParentChildLink).where(
        ParentChildLink.parent_user_id == parent_id,
        or_(
            ParentChildLink.student_id == student_id,
            ParentChildLink.student.has(StudentProfile.user_id == student_id),
        ),
    )
    link_res = await db.execute(link_stmt)
    link = link_res.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent is not linked to this student",
        )

    # Fetch student profile
    s_stmt = (
        select(StudentProfile)
        .where(or_(StudentProfile.id == student_id, StudentProfile.user_id == student_id))
        .options(selectinload(StudentProfile.user))
    )
    s_res = await db.execute(s_stmt)
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Fetch parent for preferred language
    p_stmt = select(UserAccount).where(UserAccount.id == parent_id)
    p_res = await db.execute(p_stmt)
    parent = p_res.scalar_one_or_none()
    lang = parent.preferred_lang if parent else "en"

    # Fetch student masteries
    m_stmt = (
        select(StudentMastery)
        .where(StudentMastery.student_id == student.id)
        .options(selectinload(StudentMastery.concept))
    )
    m_res = await db.execute(m_stmt)
    masteries = m_res.scalars().all()

    total_concepts = len(masteries)
    mastered = sum(1 for m in masteries if m.p_know >= 0.85)
    in_progress = sum(1 for m in masteries if 0.45 <= m.p_know < 0.85)
    needing_help = sum(1 for m in masteries if m.p_know < 0.45)
    avg_p_know = (
        sum(m.p_know for m in masteries) / total_concepts if total_concepts > 0 else 0.0
    )

    concept_details = []
    for m in masteries:
        c = m.concept
        if c:
            c_name = c.name_en
            if lang == "te" and c.name_te:
                c_name = c.name_te
            elif lang == "hi" and c.name_hi:
                c_name = c.name_hi

            concept_details.append({
                "concept_id": c.id,
                "code": c.code,
                "name": c_name,
                "concept_name": c_name,
                "p_know": m.p_know,
                "on_track": m.p_know >= 0.5,
                "status": evaluate_mastery_level(m.p_know),
                "total_attempts": m.total_attempts,
                "last_assessed_at": m.last_assessed_at,
            })

    student_name = (
        student.user.name or student.user.username if student.user else "Student"
    )

    return {
        "student_id": student.id,
        "student_name": student_name,
        "name": student_name,
        "grade": student.grade,
        "section": student.section,
        "language": lang,
        "total_xp": student.total_xp,
        "current_streak": student.current_streak,
        "longest_streak": student.longest_streak,
        "overall_mastery_pct": round(avg_p_know * 100, 1),
        "concepts_mastered": mastered,
        "concepts_in_progress": in_progress,
        "concepts_needing_help": needing_help,
        "concepts": concept_details,
        "concept_progress": concept_details,
    }


@router.post("/{parent_id}/link-child")
async def link_child_to_parent(
    parent_id: str,
    payload: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    student_username = payload.get("username", "").strip()
    relation_type = payload.get("relation_type", "parent").strip()
    if not student_username:
        raise HTTPException(status_code=400, detail="Student username is required")

    st_stmt = select(UserAccount).where(UserAccount.username == student_username, UserAccount.role == "student")
    st_user = (await db.execute(st_stmt)).scalar_one_or_none()
    if not st_user:
        raise HTTPException(status_code=404, detail="Student user not found")

    sp_stmt = select(StudentProfile).where(StudentProfile.user_id == st_user.id)
    student = (await db.execute(sp_stmt)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Check if already linked
    ex_stmt = select(ParentChildLink).where(ParentChildLink.parent_user_id == parent_id, ParentChildLink.student_id == student.id)
    existing = (await db.execute(ex_stmt)).scalar_one_or_none()
    if existing:
        return {"message": "Child already linked to parent account", "student_id": student.id}

    link = ParentChildLink(
        parent_user_id=parent_id,
        student_id=student.id,
        relation_type=relation_type,
        consent_given=True,
    )
    db.add(link)
    await db.commit()
    return {"message": f"Successfully linked {st_user.name or st_user.username}", "student_id": student.id}

