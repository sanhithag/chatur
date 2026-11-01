import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db, require_role
from app.models.assessment import LearningResource, Question
from app.models.curriculum import (
    Concept,
    CurriculumChapter,
    CurriculumSubject,
    CurriculumUnit,
)
from app.models.student import StudentProfile
from app.models.user import School, UserAccount
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.curriculum import CurriculumOverviewResponse
from app.schemas.user import SchoolCreate, SchoolResponse, UserCreate, UserResponse, UserUpdate
from app.services.auth import get_password_hash

router = APIRouter()


@router.get("/schools/{school_id}/users", response_model=PaginatedResponse[UserResponse])
async def get_school_users(
    school_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("admin", "super_admin")),
):
    query = select(UserAccount).where(UserAccount.school_id == school_id)
    if role:
        query = query.where(UserAccount.role == role)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (UserAccount.username.ilike(search_filter))
            | (UserAccount.name.ilike(search_filter))
            | (UserAccount.email.ilike(search_filter))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(UserAccount.created_at.desc())
    res = await db.execute(query)
    users = res.scalars().all()

    pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/schools/{school_id}/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_for_school(
    school_id: str,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("admin", "super_admin")),
):
    # Check if school exists
    s_stmt = select(School).where(School.id == school_id)
    s_res = await db.execute(s_stmt)
    school = s_res.scalar_one_or_none()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id '{school_id}' not found",
        )

    # Check for existing username or email
    u_stmt = select(UserAccount).where(UserAccount.username == user_in.username)
    u_res = await db.execute(u_stmt)
    if u_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already taken",
        )

    if user_in.email:
        e_stmt = select(UserAccount).where(UserAccount.email == user_in.email)
        e_res = await db.execute(e_stmt)
        if e_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_in.email}' is already in use",
            )

    new_user = UserAccount(
        school_id=school_id,
        role=user_in.role,
        username=user_in.username,
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        password_hash=get_password_hash(user_in.password),
        preferred_lang=user_in.preferred_lang,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    # If student, create StudentProfile
    if user_in.role == "student":
        student_profile = StudentProfile(
            user_id=new_user.id,
            school_id=school_id,
            grade=user_in.grade if user_in.grade is not None else 9,
            section=user_in.section if user_in.section else "A",
            roll_no=user_in.roll_no,
        )
        db.add(student_profile)

    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("admin", "super_admin")),
):
    stmt = select(UserAccount).where(UserAccount.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.preferred_lang is not None:
        user.preferred_lang = user_update.preferred_lang
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("admin", "super_admin")),
):
    stmt = select(UserAccount).where(UserAccount.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    user.is_active = False
    await db.commit()
    return MessageResponse(message=f"User '{user.username}' deactivated successfully")


@router.get("/curriculum/overview", response_model=CurriculumOverviewResponse)
async def get_curriculum_overview(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("admin", "super_admin", "teacher")),
):
    subjects_count = (await db.execute(select(func.count(CurriculumSubject.id)))).scalar_one() or 0
    units_count = (await db.execute(select(func.count(CurriculumUnit.id)))).scalar_one() or 0
    chapters_count = (await db.execute(select(func.count(CurriculumChapter.id)))).scalar_one() or 0
    concepts_count = (await db.execute(select(func.count(Concept.id)))).scalar_one() or 0
    approved_q = (
        await db.execute(
            select(func.count(Question.id)).where(Question.approval_status == "approved")
        )
    ).scalar_one() or 0
    pending_q = (
        await db.execute(
            select(func.count(Question.id)).where(
                Question.approval_status.in_(["pending_review", "draft"])
            )
        )
    ).scalar_one() or 0
    resources_count = (
        await db.execute(select(func.count(LearningResource.id)))
    ).scalar_one() or 0

    return CurriculumOverviewResponse(
        total_subjects=subjects_count,
        total_units=units_count,
        total_chapters=chapters_count,
        total_concepts=concepts_count,
        approved_questions=approved_q,
        pending_questions=pending_q,
        total_resources=resources_count,
    )


@router.get("/schools", response_model=List[SchoolResponse])
async def list_schools(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("super_admin")),
):
    stmt = select(School).order_by(School.created_at.desc())
    res = await db.execute(stmt)
    schools = res.scalars().all()
    return [SchoolResponse.model_validate(s) for s in schools]


@router.post(
    "/schools",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_school(
    school_in: SchoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(require_role("super_admin")),
):
    stmt = select(School).where(School.code == school_in.code)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"School with code '{school_in.code}' already exists",
        )

    school = School(
        name=school_in.name,
        code=school_in.code,
        is_active=True,
    )
    db.add(school)
    await db.commit()
    await db.refresh(school)
    return SchoolResponse.model_validate(school)
