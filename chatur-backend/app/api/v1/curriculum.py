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


@router.get("/subjects/{subject_id}/navigator")
async def subject_navigator(
    subject_id: str,
    grade: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    """Grades available + chapters with concept lists for one subject (single query; not the whole curriculum)."""
    from app.models import CurriculumTopic
    from app.models.lesson import ConceptLesson
    grades = [g for (g,) in (await db.execute(select(CurriculumUnit.grade).where(CurriculumUnit.subject_id == subject_id).distinct().order_by(CurriculumUnit.grade))).all()]
    if grade is None and grades:
        grade = grades[0]
    rows = (await db.execute(
        select(CurriculumUnit.name_en, CurriculumChapter.id, CurriculumChapter.chapter_no, CurriculumChapter.name_en, CurriculumChapter.name_te,
               CurriculumChapter.name_hi, Concept.id, Concept.name_en, Concept.name_te, Concept.name_hi)
        .select_from(CurriculumChapter).join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
        .join(CurriculumTopic, CurriculumTopic.chapter_id == CurriculumChapter.id).join(Concept, Concept.topic_id == CurriculumTopic.id)
        .where(CurriculumUnit.subject_id == subject_id, CurriculumUnit.grade == grade, Concept.is_active.is_(True))
        .order_by(CurriculumChapter.chapter_no, Concept.sort_order))).all()
    ready = {cid for (cid,) in (await db.execute(select(ConceptLesson.concept_id).where(ConceptLesson.status == "approved"))).all()}
    chapters: dict = {}
    for unit, chid, no, en, te, hi, cid, cen, cte, chi in rows:
        ch = chapters.setdefault(chid, {"id": chid, "chapter_no": no, "unit": unit, "name_en": en, "name_te": te, "name_hi": hi, "concepts": []})
        ch["concepts"].append({"id": cid, "name_en": cen, "name_te": cte, "name_hi": chi, "lesson_ready": cid in ready})
    return {"grades": grades, "grade": grade, "chapters": list(chapters.values())}


@router.get("/tree")
async def curriculum_tree(
    grade: Optional[int] = Query(None, description="Optional filter by grade"),
    subject_id: Optional[str] = Query(None, description="Optional filter by subject"),
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    """Full curriculum hierarchy for GeeksforGeeks-style browsing: Board -> Grade -> Subject -> Unit -> Chapter -> Topic -> Concept."""
    from app.models.curriculum import CurriculumSubject, CurriculumUnit, CurriculumChapter, CurriculumTopic, Concept

    subj_q = select(CurriculumSubject).where(CurriculumSubject.is_active.is_(True)).order_by(CurriculumSubject.sort_order)
    if subject_id:
        subj_q = subj_q.where(CurriculumSubject.id == subject_id)
    subjects = (await db.execute(subj_q)).scalars().all()

    unit_q = select(CurriculumUnit)
    if grade is not None:
        unit_q = unit_q.where(CurriculumUnit.grade == grade)
    if subject_id is not None:
        unit_q = unit_q.where(CurriculumUnit.subject_id == subject_id)
    unit_q = unit_q.order_by(CurriculumUnit.grade, CurriculumUnit.unit_no)
    units = (await db.execute(unit_q)).scalars().all()
    unit_ids = [u.id for u in units]

    chapters = []
    topics = []
    concepts = []
    if unit_ids:
        chap_q = select(CurriculumChapter).where(CurriculumChapter.unit_id.in_(unit_ids)).order_by(CurriculumChapter.chapter_no)
        chapters = (await db.execute(chap_q)).scalars().all()
        chap_ids = [ch.id for ch in chapters]
        if chap_ids:
            top_q = select(CurriculumTopic).where(CurriculumTopic.chapter_id.in_(chap_ids)).order_by(CurriculumTopic.topic_no)
            topics = (await db.execute(top_q)).scalars().all()
            top_ids = [t.id for t in topics]
            if top_ids:
                conc_q = select(Concept).where(Concept.topic_id.in_(top_ids), Concept.is_active.is_(True)).order_by(Concept.sort_order)
                concepts = (await db.execute(conc_q)).scalars().all()

    # Map topics to concepts
    concepts_by_topic: dict = {}
    for c in concepts:
        concepts_by_topic.setdefault(c.topic_id, []).append({
            "id": c.id,
            "code": c.code,
            "name_en": c.name_en,
            "name_te": c.name_te,
            "name_hi": c.name_hi,
            "grade": c.grade,
            "difficulty": c.difficulty_band,
            "objectives": c.learning_objectives or [],
        })

    # Map chapters to topics
    topics_by_chap: dict = {}
    for t in topics:
        topics_by_chap.setdefault(t.chapter_id, []).append({
            "id": t.id,
            "topic_no": t.topic_no,
            "name_en": t.name_en,
            "name_te": t.name_te,
            "name_hi": t.name_hi,
            "concepts": concepts_by_topic.get(t.id, []),
        })

    # Map units to chapters
    chaps_by_unit: dict = {}
    for ch in chapters:
        chaps_by_unit.setdefault(ch.unit_id, []).append({
            "id": ch.id,
            "chapter_no": ch.chapter_no,
            "name_en": ch.name_en,
            "name_te": ch.name_te,
            "name_hi": ch.name_hi,
            "topics": topics_by_chap.get(ch.id, []),
        })

    # Build subjects tree with grades and units
    tree = []
    for s in subjects:
        subj_units = [u for u in units if u.subject_id == s.id]
        if not subj_units:
            continue
        grades_map: dict = {}
        for u in subj_units:
            grades_map.setdefault(u.grade, []).append({
                "id": u.id,
                "unit_no": u.unit_no,
                "name_en": u.name_en,
                "name_te": u.name_te,
                "name_hi": u.name_hi,
                "chapters": chaps_by_unit.get(u.id, []),
            })
        tree.append({
            "id": s.id,
            "code": s.code,
            "name_en": s.name_en,
            "name_te": s.name_te,
            "name_hi": s.name_hi,
            "domain": s.domain,
            "grades": [
                {"grade": g, "units": ulist}
                for g, ulist in sorted(grades_map.items())
            ],
        })

    return {"tree": tree}
