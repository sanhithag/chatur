"""Verification script for the new Chatur platform features:
1. Registration & Auth RBAC
2. Global Search
3. Curriculum Hierarchy Tree
4. Topic-wise Independent Practice Module (Sessions, Submissions, History)
5. Weekly Test Persistence & Detailed Answer Review
6. Student Progress Analytics
"""
import asyncio
import os
import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import ASGITransport, AsyncClient
from app.main import app


async def test_features():
    print("============================================================")
    print("TESTING NEW CHATUR PLATFORM ARCHITECTURE & APIS")
    print("============================================================")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Registration for Student
        ts = int(time.time())
        reg_payload = {
            "username": f"student_test_{ts}",
            "password": "Password@123",
            "role": "student",
            "name": f"Pooja Sharma {ts}",
            "email": f"pooja.test.{ts}@example.com",
            "grade": 10,
            "section": "B",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201, f"Student registration failed: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        s_id = data["user"]["id"]
        print(f"[PASS] 1. Student Registration OK: {data['user']['username']} (Role: {data['user']['role']})")

        # 2. Test User Profile & Update
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        patch_res = await client.patch("/api/v1/auth/me", json={"name": "Pooja S. Sharma"}, headers=headers)
        assert patch_res.status_code == 200
        assert patch_res.json()["name"] == "Pooja S. Sharma"
        print("[PASS] 2. User Profile GET & PATCH OK")

        # 3. Test Global Search
        search_res = await client.get("/api/v1/search?q=motion", headers=headers)
        assert search_res.status_code == 200
        sdata = search_res.json()
        assert "categories" in sdata
        print(f"[PASS] 3. Global Search OK: Found {sdata['total']} items across categories")

        # 4. Test Curriculum Hierarchy Tree
        tree_res = await client.get("/api/v1/curriculum/tree", headers=headers)
        assert tree_res.status_code == 200
        tdata = tree_res.json()
        assert "tree" in tdata and len(tdata["tree"]) > 0
        print(f"[PASS] 4. Curriculum Tree OK: Found {len(tdata['tree'])} subjects in hierarchy")

        # 5. Test Practice Filters
        filt_res = await client.get(f"/api/v1/students/{s_id}/practice/filters", headers=headers)
        assert filt_res.status_code == 200
        fdata = filt_res.json()
        assert "grades" in fdata
        print(f"[PASS] 5. Practice Filters OK: Available grades: {[g['grade'] for g in fdata['grades']]}")

        # 6. Test Practice Session Creation & Submission
        sess_req = {
            "grade": 9,
            "difficulty": "medium",
            "count": 3,
        }
        sess_res = await client.post(f"/api/v1/students/{s_id}/practice/session", json=sess_req, headers=headers)
        assert sess_res.status_code == 200
        p_sess = sess_res.json()
        assert len(p_sess["questions"]) > 0
        q0 = p_sess["questions"][0]
        print(f"[PASS] 6a. Practice Session Created OK: {len(p_sess['questions'])} questions retrieved")

        # Submit practice session
        submit_sess_req = {
            "session_id": p_sess["session_id"],
            "responses": [
                {"question_id": q["id"], "selected_option": 0, "hints_used": 1, "time_spent_secs": 15}
                for q in p_sess["questions"]
            ]
        }
        p_sub_res = await client.post(f"/api/v1/students/{s_id}/practice/session/submit", json=submit_sess_req, headers=headers)
        assert p_sub_res.status_code == 200
        p_result = p_sub_res.json()
        assert "score" in p_result and "accuracy_pct" in p_result
        print(f"[PASS] 6b. Practice Session Submitted OK: Score {p_result['score']}/{p_result['total']} ({p_result['accuracy_pct']}%)")

        # 7. Test Practice History
        hist_res = await client.get(f"/api/v1/students/{s_id}/practice/history", headers=headers)
        assert hist_res.status_code == 200
        hdata = hist_res.json()
        assert len(hdata) >= 1
        print(f"[PASS] 7. Practice History OK: Recorded {len(hdata)} past practice sessions in DB")

        # 8. Test Weekly Test Listing
        tlist_res = await client.get(f"/api/v1/students/{s_id}/test/list", headers=headers)
        assert tlist_res.status_code == 200
        tlist = tlist_res.json()
        assert len(tlist["available"]) > 0
        print(f"[PASS] 8. Weekly Test List OK: {len(tlist['available'])} available, {len(tlist['upcoming'])} upcoming")

        # 9. Test Weekly Test Submission & Persistence
        active_t_res = await client.get(f"/api/v1/students/{s_id}/test/active", headers=headers)
        assert active_t_res.status_code == 200
        paper = active_t_res.json()
        test_sub_payload = {
            "assessment_id": paper["assessment_id"],
            "responses": [
                {"question_id": it["question_id"], "selected_option": 0}
                for it in paper["items"][:5]
            ]
        }
        t_sub_res = await client.post(f"/api/v1/students/{s_id}/test/submit", json=test_sub_payload, headers=headers)
        assert t_sub_res.status_code == 200
        t_sub_data = t_sub_res.json()
        assert "attempt_id" in t_sub_data and t_sub_data["attempt_id"] is not None
        attempt_id = t_sub_data["attempt_id"]
        print(f"[PASS] 9a. Weekly Test Submitted & Persisted OK: Attempt ID {attempt_id}")

        # Review attempt
        rev_res = await client.get(f"/api/v1/students/{s_id}/test/attempts/{attempt_id}", headers=headers)
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert len(rev_data["questions"]) == 5
        print(f"[PASS] 9b. Weekly Test Attempt Review OK: Retrieved {len(rev_data['questions'])} reviewed questions")

        # 10. Test Student Progress Summary
        prog_res = await client.get(f"/api/v1/students/{s_id}/progress/summary", headers=headers)
        assert prog_res.status_code == 200
        prog_data = prog_res.json()
        assert "overall_mastery_pct" in prog_data
        assert len(prog_data["subjects"]) > 0
        print(f"[PASS] 10. Student Progress Summary OK: {len(prog_data['subjects'])} subjects tracked")

        print("============================================================")
        print("ALL NEW BACKEND CAPABILITIES VERIFIED SUCCESSFULLY!")
        print("============================================================")


if __name__ == "__main__":
    asyncio.run(test_features())
