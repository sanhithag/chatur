"""Retrieve approved stored lessons first; translate with persistent cache and graceful fallback."""
import copy
import json
import logging
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lesson import ConceptLesson, GenerationLog, LessonTranslation
from app.services import ai_provider
from app.services.lesson_schema import SCHEMA_HINT, validate_lesson

log = logging.getLogger(__name__)
LANG_NAMES = {"te": "Telugu", "hi": "Hindi"}

GEN_SYSTEM = ("You write ORIGINAL school lessons for CBSE students, grounded in the supplied reference excerpt. "
              "Never copy textbook sentences. Be factually accurate and grade-appropriate. "
              "The five styles must be genuinely different: simple, detailed, visual (describe a diagram), "
              "real-world analogy, worked example. Return ONLY JSON matching this schema:\n" + SCHEMA_HINT)
TR_SYSTEM = ("You translate school lessons into {lang} for the given grade. Use natural, student-friendly {lang}. "
             "Keep ALL numbers, units, formulas, equations, chemical formulas, symbols and JSON keys unchanged. "
             "Where useful, keep the English technical term in brackets after the {lang} term. "
             "Translate every string value (including options, hints, explanations). Return ONLY the same JSON structure. "
             "Do not translate the fields check_expr/check_value.")


async def get_approved_lesson(db: AsyncSession, concept_id: str) -> Optional[ConceptLesson]:
    r = await db.execute(select(ConceptLesson).where(ConceptLesson.concept_id == concept_id, ConceptLesson.status == "approved")
                         .order_by(ConceptLesson.version.desc()).limit(1))
    return r.scalar_one_or_none()


def _same_shape(a: Any, b: Any) -> bool:
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_same_shape(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_same_shape(x, y) for x, y in zip(a, b))
    return True


def _preserve(src: Dict[str, Any], tr: Dict[str, Any]) -> Dict[str, Any]:
    """Structural guarantees: answer keys / verification fields always come from the source."""
    out = copy.deepcopy(tr)
    if "comprehension" in out:
        out["comprehension"]["correct_index"] = src["comprehension"]["correct_index"]
    for s, t in zip(src.get("practice", []), out.get("practice", [])):
        for k in ("correct_index", "check_expr", "check_value"):
            if k in s:
                t[k] = s[k]
    return out


async def translate_lesson(db: AsyncSession, lesson: ConceptLesson, lang: str, grade: int) -> Optional[LessonTranslation]:
    """Translate and cache. Returns None (never raises) if the provider is unavailable."""
    try:
        data = await ai_provider.generate_json(TR_SYSTEM.format(lang=LANG_NAMES[lang]),
                                               f"Grade {grade}. Translate this lesson:\n{json.dumps(lesson.content, ensure_ascii=False)}")
    except ai_provider.AIUnavailable as e:
        db.add(GenerationLog(concept_id=lesson.concept_id, action="translate", ok=0, detail=f"{lang}: {e}"))
        await db.commit()
        return None
    if not _same_shape(lesson.content.get("styles"), data.get("styles")) or not _same_shape(lesson.content.get("practice"), data.get("practice")):
        db.add(GenerationLog(concept_id=lesson.concept_id, action="translate", ok=0, detail=f"{lang}: structure mismatch"))
        await db.commit()
        return None
    content = _preserve(lesson.content, data)
    r = await db.execute(select(LessonTranslation).where(LessonTranslation.lesson_id == lesson.id, LessonTranslation.lang == lang))
    row = r.scalar_one_or_none()
    if row:
        row.content, row.source_version, row.provider = content, lesson.version, "ai"
    else:
        row = LessonTranslation(lesson_id=lesson.id, lang=lang, source_version=lesson.version, content=content, provider="ai")
        db.add(row)
    db.add(GenerationLog(concept_id=lesson.concept_id, action="translate", ok=1, detail=lang))
    await db.commit()
    if lesson.status == "approved":
        await sync_questions(db, lesson)
    return row


async def get_lesson_for_language(db: AsyncSession, lesson: ConceptLesson, lang: str, grade: int, allow_live_translate: bool = True) -> Tuple[Dict[str, Any], str, bool]:
    """Returns (content, language_served, fallback_used)."""
    if lang == "en" or lang not in LANG_NAMES:
        return lesson.content, "en", False
    r = await db.execute(select(LessonTranslation).where(LessonTranslation.lesson_id == lesson.id, LessonTranslation.lang == lang))
    row = r.scalar_one_or_none()
    if row and row.source_version == lesson.version:
        return row.content, lang, False
    if allow_live_translate and ai_provider.is_configured():
        row = await translate_lesson(db, lesson, lang, grade)
        if row:
            return row.content, lang, False
    return lesson.content, "en", True


async def generate_lesson(db: AsyncSession, concept, chapter_name: str, topic_name: str, subject: str, reference: str, sources) -> ConceptLesson:
    """Generate one lesson for one concept; stored as 'generated' or 'validated' (never auto-approved)."""
    prompt = (f"Class {concept.grade} {subject}. Chapter: {chapter_name}. Topic: {topic_name}. Concept: {concept.name_en}.\n"
              f"Learning objectives hint: {concept.learning_objectives or 'derive from the reference'}.\n"
              f"Reference excerpt (do not copy):\n{reference[:6000] or '(none available; stay strictly within the class syllabus)'}\n"
              "Write 1 comprehension MCQ and 4 practice MCQs of increasing difficulty with hints.")
    content = await ai_provider.generate_json(GEN_SYSTEM, prompt)
    report = validate_lesson(content, concept.name_en)
    r = await db.execute(select(ConceptLesson).where(ConceptLesson.concept_id == concept.id).order_by(ConceptLesson.version.desc()).limit(1))
    prev = r.scalar_one_or_none()
    lesson = ConceptLesson(concept_id=concept.id, version=(prev.version + 1) if prev else 1, content=content,
                           status="validated" if report["ok"] else "generated", validation_report=report,
                           sources=sources, provider=f"ai:{__import__('app.config', fromlist=['settings']).settings.ai_provider}")
    db.add(lesson)
    db.add(GenerationLog(concept_id=concept.id, action="generate", ok=1 if report["ok"] else 0, detail=json.dumps(report)[:500]))
    await db.commit()
    return lesson


async def sync_questions(db: AsyncSession, lesson: ConceptLesson) -> int:
    """Mirror an approved lesson's practice items into Question rows so existing Solve/Test/BKT work unchanged.
    Idempotent: rows are keyed by source=f'lesson:{lesson.id}' and rebuilt, including te/hi text when translations exist."""
    from sqlalchemy import delete
    from app.models.assessment import Question
    trs = {t.lang: t.content for t in (await db.execute(select(LessonTranslation).where(
        LessonTranslation.lesson_id == lesson.id, LessonTranslation.source_version == lesson.version))).scalars().all()}
    src = f"lesson:{lesson.id}"
    await db.execute(delete(Question).where(Question.source == src))
    items = [(lesson.content["practice"][i], i) for i in range(len(lesson.content.get("practice", [])))]
    for q, i in items:
        def tr(lang, key):
            try: return trs[lang]["practice"][i][key]
            except (KeyError, IndexError): return None
        diff = 0.25 + 0.5 * (i / max(1, len(items) - 1))
        db.add(Question(
            concept_id=lesson.concept_id, qtype="mcq", difficulty=round(diff, 2), usage_tag="practice", bloom_level="apply" if i else "understand",
            body_en={"text": q["question"]}, body_te={"text": tr("te", "question")} if tr("te", "question") else None,
            body_hi={"text": tr("hi", "question")} if tr("hi", "question") else None,
            answer_data={"options": q["options"], "correct_index": q["correct_index"]},
            explanation_en=q["explanation"], explanation_te=tr("te", "explanation"), explanation_hi=tr("hi", "explanation"),
            hints=[q["hint"]], source=src, approval_status="approved"))
    await db.commit()
    return len(items)
