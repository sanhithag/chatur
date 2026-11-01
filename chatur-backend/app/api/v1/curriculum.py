from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.models.curriculum import (
    Board,
    Concept,
    CurriculumChapter,
    CurriculumSubject,
    CurriculumUnit,
)
from app.models.user import UserAccount
from app.schemas.curriculum import (
    ChapterWithTopicsResponse,
    ConceptChainStep,
    ConceptDetailResponse,
    PrerequisiteItem,
    SubjectResponse,
    TopicResponse,
)
from app.services.curriculum import get_immediate_prerequisites, get_prerequisite_chain

router = APIRouter()


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    board_code: Optional[str] = Query(None, description="Board code filter, e.g. CBSE"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    query = select(CurriculumSubject).where(CurriculumSubject.is_active.is_(True))
    if board_code:
        query = query.join(Board, CurriculumSubject.board_id == Board.id).where(
            Board.code == board_code
        )
    query = query.order_by(CurriculumSubject.sort_order)
    res = await db.execute(query)
    subjects = res.scalars().all()
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.get(
    "/subjects/{subject_id}/chapters",
    response_model=List[ChapterWithTopicsResponse],
)
async def list_subject_chapters(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = (
        select(CurriculumChapter)
        .join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .where(CurriculumUnit.subject_id == subject_id)
        .options(selectinload(CurriculumChapter.topics))
        .order_by(CurriculumChapter.chapter_no)
    )
    res = await db.execute(stmt)
    chapters = res.scalars().all()

    results = []
    for ch in chapters:
        topics = [
            TopicResponse(
                id=t.id,
                chapter_id=t.chapter_id,
                topic_no=t.topic_no,
                name_en=t.name_en,
                name_te=t.name_te,
                name_hi=t.name_hi,
            )
            for t in ch.topics
        ]
        results.append(
            ChapterWithTopicsResponse(
                id=ch.id,
                unit_id=ch.unit_id,
                chapter_no=ch.chapter_no,
                name_en=ch.name_en,
                name_te=ch.name_te,
                name_hi=ch.name_hi,
                ncert_verified=ch.ncert_verified,
                topics=topics,
            )
        )
    return results


@router.get("/concepts/{concept_id}", response_model=ConceptDetailResponse)
async def get_concept_detail(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    stmt = select(Concept).where(Concept.id == concept_id)
    res = await db.execute(stmt)
    concept = res.scalar_one_or_none()
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id '{concept_id}' not found",
        )
    return ConceptDetailResponse.model_validate(concept)


@router.get(
    "/concepts/{concept_id}/prerequisites",
    response_model=List[PrerequisiteItem],
)
async def get_concept_prerequisites(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    prereqs = await get_immediate_prerequisites(db, concept_id)
    return [PrerequisiteItem(**p) for p in prereqs]


@router.get("/concepts/{concept_id}/chain", response_model=List[ConceptChainStep])
async def get_concept_chain(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    chain = await get_prerequisite_chain(db, concept_id)
    return [
        ConceptChainStep(
            id=c["id"],
            code=c["code"],
            name_en=c["name_en"],
            name_te=c.get("name_te"),
            name_hi=c.get("name_hi"),
            grade=c["grade"],
            difficulty_band=c["difficulty_band"],
        )
        for c in chain
    ]


@router.get("/graph")
async def get_curriculum_graph(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    """Returns the full Directed Acyclic Graph (DAG) of cross-grade concept prerequisites."""
    from app.models.curriculum import ConceptPrerequisite

    c_stmt = select(Concept).where(Concept.is_active.is_(True)).order_by(Concept.grade, Concept.sort_order)
    c_res = await db.execute(c_stmt)
    concepts = c_res.scalars().all()

    p_stmt = select(ConceptPrerequisite)
    p_res = await db.execute(p_stmt)
    prereqs = p_res.scalars().all()

    nodes = [
        {
            "id": c.id,
            "code": c.code,
            "name": c.name_en,
            "name_te": c.name_te,
            "name_hi": c.name_hi,
            "grade": c.grade,
            "difficulty": c.difficulty_band,
            "objectives": c.learning_objectives or [],
        }
        for c in concepts
    ]

    edges = [
        {
            "id": f"{p.prerequisite_id}->{p.concept_id}",
            "source": p.prerequisite_id,
            "target": p.concept_id,
            "is_strict": p.is_strict,
            "weight": p.weight,
        }
        for p in prereqs
    ]

    return {"nodes": nodes, "edges": edges}
