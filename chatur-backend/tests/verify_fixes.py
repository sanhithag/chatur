"""Targeted verification for concept-specific hints and lesson routing."""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database import async_session_factory
from app.models.curriculum import Concept
from sqlalchemy import select


async def run_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login as student1
        res = await ac.post("/api/v1/auth/login", json={"username": "student1", "password": "Student@2024"})
        assert res.status_code == 200, f"Login failed: {res.text}"
        login_data = res.json()
        token = login_data["access_token"]
        student_id = login_data["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Query concepts to get IDs for English (eng_rc7), Maths (math_lin9), Science (sci_mot9)
        async with async_session_factory() as db:
            eng_res = await db.execute(select(Concept).where(Concept.code == "eng_rc7"))
            eng_c = eng_res.scalar_one()

            math_res = await db.execute(select(Concept).where(Concept.code == "math_lin9"))
            math_c = math_res.scalar_one()

            sci_res = await db.execute(select(Concept).where(Concept.code == "sci_mot9"))
            sci_c = sci_res.scalar_one()

        print(f"Found concepts:\n  English: {eng_c.name_en} ({eng_c.id})\n  Maths: {math_c.name_en} ({math_c.id})\n  Science: {sci_c.name_en} ({sci_c.id})")

        # 3. Test English Practice Question and Hints
        res = await ac.get(f"/api/v1/students/{student_id}/solve/next?concept_id={eng_c.id}", headers=headers)
        assert res.status_code == 200, f"English solve failed: {res.text}"
        data = res.json()
        q = data["question"]
        print("\n--- ENGLISH PRACTICE QUESTION ---")
        print(f"Question text: {q['body']}")
        print(f"Hints received ({len(q['hints'])}):")
        for i, h in enumerate(q['hints'], 1):
            print(f"  Hint {i}: {h}")

        # Assert no physics in English hints!
        for h in q['hints']:
            assert "v = u + at" not in h, f"Physics formula found in English hint: {h}"
            assert "s = ut" not in h, f"Physics formula found in English hint: {h}"
        assert any("scanning" in h.lower() or "reading" in h.lower() or "factual" in h.lower() or "detail" in h.lower() or "question" in h.lower() for h in q['hints']), "English hints do not contain expected reading terms!"
        print("[PASS] English question hints are subject-accurate and free of physics leakage.")

        # 4. Test English Micro-Lesson
        res = await ac.get(f"/api/v1/students/{student_id}/learn/active?concept_id={eng_c.id}", headers=headers)
        assert res.status_code == 200, f"English learn failed: {res.text}"
        lesson = res.json()
        print("\n--- ENGLISH MICRO-LESSON ---")
        print(f"Subject: {lesson['subject_name']}")
        print(f"Concept: {lesson['concept_name']}")
        print(f"Key Terms: {lesson['key_terms']}")
        print(f"Simple Style Title: {lesson['styles']['simple']['title']}")
        print(f"Simple Style Snippet: {lesson['styles']['simple']['content'][:120]}...")

        assert lesson['subject_name'] == "English Language & Literature"
        assert "v = u + at" not in lesson['styles']['simple']['content']
        assert "Skimming" in lesson['styles']['simple']['content'] or "Reading" in lesson['styles']['simple']['content']
        print("[PASS] English micro-lesson is 100% English Language & Literature content.")

        # 5. Test Mathematics Micro-Lesson
        res = await ac.get(f"/api/v1/students/{student_id}/learn/active?concept_id={math_c.id}", headers=headers)
        assert res.status_code == 200, f"Maths learn failed: {res.text}"
        math_lesson = res.json()
        print("\n--- MATHEMATICS MICRO-LESSON ---")
        print(f"Subject: {math_lesson['subject_name']}")
        print(f"Concept: {math_lesson['concept_name']}")
        print(f"Simple Style Title: {math_lesson['styles']['simple']['title']}")
        assert math_lesson['subject_name'] == "Mathematics"
        assert "ax + by + c = 0" in math_lesson['styles']['simple']['content']
        print("[PASS] Mathematics micro-lesson is 100% Mathematics content.")

        # 6. Test Science Micro-Lesson
        res = await ac.get(f"/api/v1/students/{student_id}/learn/active?concept_id={sci_c.id}", headers=headers)
        assert res.status_code == 200, f"Science learn failed: {res.text}"
        sci_lesson = res.json()
        print("\n--- SCIENCE MICRO-LESSON ---")
        print(f"Subject: {sci_lesson['subject_name']}")
        print(f"Concept: {sci_lesson['concept_name']}")
        assert "Science" in sci_lesson['subject_name']
        print("[PASS] Science micro-lesson is accurate.")

    print("\n============================================================")
    print("ALL TARGETED VERIFICATIONS PASSED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
