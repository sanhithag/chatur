from typing import Any, Dict, List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.curriculum import Concept, ConceptPrerequisite


async def get_prerequisite_chain(
    db: AsyncSession, concept_id: str
) -> List[Dict[str, Any]]:
    """Traverses prerequisite relationships backwards to find all ancestor concepts

    in dependency order (from earliest foundational prerequisite up to the
    target concept).
    """
    visited: Set[str] = set()
    chain: List[Dict[str, Any]] = []

    async def traverse(current_id: str):
        if current_id in visited:
            return
        visited.add(current_id)

        # Get prerequisites of current_id
        stmt = (
            select(ConceptPrerequisite)
            .where(ConceptPrerequisite.concept_id == current_id)
            .options(selectinload(ConceptPrerequisite.prerequisite))
        )
        result = await db.execute(stmt)
        prereqs = result.scalars().all()

        for pr in prereqs:
            await traverse(pr.prerequisite_id)

        # Get concept details
        c_stmt = (
            select(Concept)
            .where(Concept.id == current_id)
            .options(selectinload(Concept.topic))
        )
        c_res = await db.execute(c_stmt)
        concept = c_res.scalar_one_or_none()

        if concept and not any(item["id"] == concept.id for item in chain):
            chain.append({
                "id": concept.id,
                "code": concept.code,
                "name_en": concept.name_en,
                "name_te": concept.name_te,
                "name_hi": concept.name_hi,
                "grade": concept.grade,
                "difficulty_band": concept.difficulty_band,
                "topic_id": concept.topic_id,
                "is_active": concept.is_active,
            })

    await traverse(concept_id)
    return chain


async def get_immediate_prerequisites(
    db: AsyncSession, concept_id: str
) -> List[Dict[str, Any]]:
    """Fetches direct prerequisites of a given concept."""
    stmt = (
        select(ConceptPrerequisite)
        .where(ConceptPrerequisite.concept_id == concept_id)
        .options(selectinload(ConceptPrerequisite.prerequisite))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for r in records:
        prereq = r.prerequisite
        if prereq:
            items.append({
                "prerequisite_id": prereq.id,
                "code": prereq.code,
                "name_en": prereq.name_en,
                "grade": prereq.grade,
                "is_strict": r.is_strict,
                "weight": r.weight,
            })
    return items


async def get_dependent_concepts(
    db: AsyncSession, concept_id: str
) -> List[Dict[str, Any]]:
    """Fetches concepts that directly require this concept as a prerequisite."""
    stmt = (
        select(ConceptPrerequisite)
        .where(ConceptPrerequisite.prerequisite_id == concept_id)
        .options(selectinload(ConceptPrerequisite.concept))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for r in records:
        c = r.concept
        if c:
            items.append({
                "dependent_concept_id": c.id,
                "code": c.code,
                "name_en": c.name_en,
                "grade": c.grade,
                "is_strict": r.is_strict,
            })
    return items
