"""Tests for subject switching, lesson retrieval, translation cache/fallback, approval flow.
The AI provider is MOCKED here to test logic; generated text is placeholder test data, not curriculum content."""
import asyncio, copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services import ai_provider
from app.services.lesson_schema import validate_lesson

def fake_lesson(name):
    mcq = lambda i: {"question": f"Q{i} on {name}?", "options": ["2", "4", "6", "8"], "correct_index": 1, "hint": "add", "explanation": "2+2=4", "check_expr": "2+2", "check_value": 4}
    return {"title": name, "introduction": "intro", "objectives": ["o"], "styles": {k: f"{k} explanation of {name} with enough detail to pass checks." for k in ["simple", "detailed", "visual", "analogy", "worked"]},
            "key_terms": ["t"], "definitions": [{"term": "t", "meaning": "m"}], "misconceptions": [], "summary": "s",
            "comprehension": {"question": "c?", "options": ["a", "b"], "correct_index": 0, "explanation": "e"}, "practice": [mcq(1), mcq(2), mcq(3)]}

def tr(d):
    d = copy.deepcopy(d)
    def walk(x):
        if isinstance(x, dict): return {k: (v if k in ("check_expr", "check_value", "correct_index") else walk(v)) for k, v in x.items()}
        if isinstance(x, list): return [walk(i) for i in x]
        return f"[TR]{x}" if isinstance(x, str) else x
    return walk(d)

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        H = lambda r: {"Authorization": f"Bearer {r.json()['access_token']}"}
        adm = H(await c.post("/api/v1/auth/login", json={"username": "superadmin", "password": "Admin@CHATUR2024"}))
        sres = await c.post("/api/v1/auth/login", json={"username": "student1", "password": "Student@2024"})
        st = H(sres); sid = sres.json()["user"]["id"]
        subs = {s["code"]: s["id"] for s in (await c.get("/api/v1/curriculum/subjects", headers=st)).json()}
        assert {"MATH", "SCI", "SST", "ENG"} <= set(subs), subs
        print("[PASS] subjects from backend:", sorted(subs))
        # SUBJECT SWITCHING: each selected subject must return a concept of that subject
        for code in ("MATH", "SCI", "SST", "ENG"):
            r = await c.get(f"/api/v1/students/{sid}/learn/active?subject_id={subs[code]}", headers=st)
            assert r.status_code == 200, r.text
            assert r.json()["subject_id"] == subs[code], (code, r.json()["subject_id"])
        print("[PASS] subject switching returns same-subject concepts (MATH, SCI, SST, ENG)")
        nav = (await c.get(f"/api/v1/curriculum/subjects/{subs['MATH']}/navigator?grade=10", headers=st)).json()
        assert len(nav["chapters"]) == 14, len(nav["chapters"])
        print("[PASS] navigator: Class 10 Maths has", len(nav["chapters"]), "chapters")
        prog = (await c.get(f"/api/v1/students/{sid}/subjects/progress", headers=st)).json()
        assert all(p["concepts"] > 0 for p in prog); print("[PASS] subject progress:", [(p["name_en"], p["concepts"], p["mastered"]) for p in prog])
        # pending lesson is explicit, not generic
        cid = nav["chapters"][0]["concepts"][0]["id"]
        r = (await c.get(f"/api/v1/students/{sid}/learn/active?concept_id={cid}", headers=st)).json()
        assert r["lesson_source"] == "pending"; print("[PASS] unpopulated concept reports 'pending'")
        # generate (mocked) -> validate -> approve -> student sees it
        async def fake_gen(system, prompt):
            return fake_lesson("Real Numbers") if "Translate" not in prompt else tr(fake_lesson("Real Numbers"))
        ai_provider.generate_json = fake_gen; ai_provider.is_configured = lambda: True
        g = await c.post(f"/api/v1/admin/content/generate/{cid}", headers=adm); assert g.status_code == 200, g.text
        assert g.json()["status"] == "validated"
        lid = g.json()["id"]
        a = await c.post(f"/api/v1/admin/content/lessons/{lid}/status", json={"status": "approved"}, headers=adm); assert a.status_code == 200, a.text
        assert a.json()["questions_synced"] == 3
        r = (await c.get(f"/api/v1/students/{sid}/learn/active?concept_id={cid}&lang=en", headers=st)).json()
        assert r["lesson_source"] == "stored" and r["styles"]["worked"]["title"]; print("[PASS] approved lesson served; practice synced to Solve/Test questions")
        # translation: live translate + cache, then provider down -> cached still served
        r = (await c.get(f"/api/v1/students/{sid}/learn/active?concept_id={cid}&lang=te", headers=st)).json()
        assert r["language_served"] == "te" and r["styles"]["simple"]["content"].startswith("[TR]") and not r["translation_fallback"]
        calls = {"n": 0}
        async def down(*a, **k): calls["n"] += 1; raise ai_provider.AIUnavailable("down")
        ai_provider.generate_json = down
        r = (await c.get(f"/api/v1/students/{sid}/learn/active?concept_id={cid}&lang=te", headers=st)).json()
        assert r["language_served"] == "te" and calls["n"] == 0; print("[PASS] translation cached; provider not re-called")
        r = (await c.get(f"/api/v1/students/{sid}/learn/active?concept_id={cid}&lang=hi", headers=st)).json()
        assert r["language_served"] == "en" and r["translation_fallback"] is True and r["styles"]["simple"]["content"]
        print("[PASS] AI down + uncached language -> English fallback flagged, no crash")
        cov = (await c.get("/api/v1/admin/content/coverage", headers=adm)).json(); assert any(x["approved"] for x in cov); print("[PASS] admin coverage:", [x for x in cov if x["approved"]])
        bad = fake_lesson("x"); bad["practice"][0]["check_value"] = 5
        assert not validate_lesson(bad)["ok"]; print("[PASS] arithmetic verification catches wrong answer")
        # RBAC
        assert (await c.get("/api/v1/admin/content/coverage", headers=st)).status_code == 403; print("[PASS] students cannot access admin content API")

asyncio.run(main())
