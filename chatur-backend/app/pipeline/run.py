"""Resumable content pipeline.
  python -m app.pipeline.run seed                          # import verified curriculum (idempotent)
  python -m app.pipeline.run generate --subject MATH --grade 10 [--limit 5]   # skips concepts that already have a lesson
  python -m app.pipeline.run translate --lang te,hi [--subject SCI]            # only approved lessons lacking fresh translation
  python -m app.pipeline.run report                        # exact counts
Admins approve lessons via /api/v1/admin/content/lessons/{id}/status.
"""
import argparse
import asyncio
import json
import subprocess
from pathlib import Path
from sqlalchemy import func, select
from app.config import settings
from app.database import async_session_factory
from app.models import Board, Concept, CurriculumChapter, CurriculumSubject, CurriculumTopic, CurriculumUnit
from app.models.lesson import ConceptLesson, LessonTranslation
from app.services import ai_provider, lesson_service

DATA = Path(__file__).resolve().parent.parent / "data" / "verified_curriculum.json"
SUBJECTS = {"MATH": ("Mathematics", "గణితం", "गणित", "mathematics", 1), "SCI": ("Science", "సైన్స్", "विज्ञान", "science", 2),
            "ENG": ("English Language & Literature", "ఇంగ్లీష్", "अंग्रेज़ी", "english", 3), "SST": ("Social Science", "సాంఘిక శాస్త్రం", "सामाजिक विज्ञान", "social_science", 5)}


async def seed():
    async with async_session_factory() as db:
        board = (await db.execute(select(Board).where(Board.code == "CBSE"))).scalar_one_or_none()
        if not board:
            board = Board(code="CBSE", name="Central Board of Secondary Education"); db.add(board); await db.flush()
        made = 0
        for entry in json.loads(DATA.read_text(encoding="utf-8")):
            sc = entry["subject"]
            subj = (await db.execute(select(CurriculumSubject).where(CurriculumSubject.board_id == board.id, CurriculumSubject.code == sc))).scalar_one_or_none()
            if not subj:
                n = SUBJECTS[sc]; subj = CurriculumSubject(board_id=board.id, code=sc, name_en=n[0], name_te=n[1], name_hi=n[2], domain=n[3], sort_order=n[4]); db.add(subj); await db.flush()
            for u in entry["units"]:
                unit = (await db.execute(select(CurriculumUnit).where(CurriculumUnit.subject_id == subj.id, CurriculumUnit.grade == entry["grade"], CurriculumUnit.name_en == u["name"]))).scalar_one_or_none()
                if not unit:
                    unit = CurriculumUnit(subject_id=subj.id, grade=entry["grade"], academic_year="2026-27", unit_no=u["unit_no"], name_en=u["name"], source_ref=entry["source"]); db.add(unit); await db.flush()
                for ch in u["chapters"]:
                    chap = (await db.execute(select(CurriculumChapter).where(CurriculumChapter.unit_id == unit.id, CurriculumChapter.chapter_no == ch["no"]))).scalar_one_or_none()
                    if not chap:
                        chap = CurriculumChapter(unit_id=unit.id, chapter_no=ch["no"], name_en=ch["name"], source_ref=entry["source"], ncert_verified=True); db.add(chap); await db.flush()
                    topics = ch["topics"] or [ch["name"]]
                    for ti, tn in enumerate(topics, 1):
                        code = f"NC{entry['grade']}-{sc}-{ch['no']:02d}-{ti:02d}"
                        if (await db.execute(select(Concept.id).where(Concept.code == code))).first():
                            continue
                        topic = CurriculumTopic(chapter_id=chap.id, topic_no=ti, name_en=tn); db.add(topic); await db.flush()
                        db.add(Concept(topic_id=topic.id, code=code, name_en=tn, grade=entry["grade"], difficulty_band="medium",
                                       learning_objectives=[], common_misconceptions=[], content_status="draft", sort_order=ch["no"] * 100 + ti))
                        made += 1
        await db.commit()
        print(f"seed complete: {made} new concepts")


def _reference(chapter: CurriculumChapter, grade: int, sc: str) -> str:
    if not settings.reference_dir:
        return ""
    prefix = {("SCI", 10): "jesc1", ("MATH", 10): "jemh1", ("SST", 9): "iest1", ("ENG", 9): "iebe1"}.get((sc, grade))
    p = Path(settings.reference_dir) / f"{prefix}{chapter.chapter_no:02d}.pdf" if prefix else None
    if p and p.exists():
        return subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True).stdout
    return ""


async def _concept_rows(db, subject, grade):
    q = (select(Concept, CurriculumTopic, CurriculumChapter, CurriculumSubject).join(CurriculumTopic, Concept.topic_id == CurriculumTopic.id)
         .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id).join(CurriculumUnit, CurriculumChapter.unit_id == CurriculumUnit.id)
         .join(CurriculumSubject, CurriculumUnit.subject_id == CurriculumSubject.id).where(Concept.code.like("NC%")).order_by(Concept.sort_order))
    if subject: q = q.where(CurriculumSubject.code == subject)
    if grade: q = q.where(Concept.grade == grade)
    return (await db.execute(q)).all()


async def generate(subject, grade, limit):
    if not ai_provider.is_configured():
        print("No AI provider configured. Set AI_PROVIDER and the key in .env. Nothing generated."); return
    done = 0
    async with async_session_factory() as db:
        for c, t, ch, s in await _concept_rows(db, subject, grade):
            if (await db.execute(select(ConceptLesson.id).where(ConceptLesson.concept_id == c.id))).first():
                continue  # resumable: no duplicates
            try:
                await lesson_service.generate_lesson(db, c, ch.name_en, t.name_en, s.name_en, _reference(ch, c.grade, s.code), [ch.source_ref])
                done += 1; print("generated", c.code)
            except ai_provider.AIUnavailable as e:
                print("failed", c.code, e)
            if limit and done >= limit: break
    print("generated:", done)


async def translate(langs, subject):
    n = 0
    async with async_session_factory() as db:
        for c, t, ch, s in await _concept_rows(db, subject, None):
            lesson = await lesson_service.get_approved_lesson(db, c.id)
            if not lesson: continue
            for lang in langs:
                tr = (await db.execute(select(LessonTranslation).where(LessonTranslation.lesson_id == lesson.id, LessonTranslation.lang == lang))).scalar_one_or_none()
                if tr and tr.source_version == lesson.version: continue
                if await lesson_service.translate_lesson(db, lesson, lang, c.grade): n += 1; print("translated", c.code, lang)
    print("translations:", n)


async def report():
    async with async_session_factory() as db:
        rows = await _concept_rows(db, None, None)
        print("verified curriculum concepts:", len(rows))
        for st in ("generated", "validated", "approved"):
            print(st, (await db.execute(select(func.count()).select_from(ConceptLesson).where(ConceptLesson.status == st))).scalar())
        for lg in ("te", "hi"):
            print("translations", lg, (await db.execute(select(func.count()).select_from(LessonTranslation).where(LessonTranslation.lang == lg))).scalar())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["seed", "generate", "translate", "report"])
    ap.add_argument("--subject"); ap.add_argument("--grade", type=int); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--lang", default="te,hi")
    a = ap.parse_args()
    if a.cmd == "seed": coro = seed()
    elif a.cmd == "report": coro = report()
    elif a.cmd == "generate": coro = generate(a.subject, a.grade, a.limit)
    else: coro = translate(a.lang.split(","), a.subject)
    asyncio.run(coro)


if __name__ == "__main__":
    main()
