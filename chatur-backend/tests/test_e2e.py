import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import AsyncClient, ASGITransport
from app.main import app

async def run_tests():
    print("=" * 60)
    print("STARTING CHATUR BACKEND INTEGRATION & VERIFICATION TESTS")
    print("=" * 60)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] 1. Health Check: OK ->", res.json())

        # 2. Login Superadmin
        login_res = await client.post("/api/v1/auth/login", json={"username": "superadmin", "password": "Admin@CHATUR2024"})
        assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
        admin_data = login_res.json()
        admin_token = admin_data["access_token"]
        print("[PASS] 2. Superadmin Login: OK -> Role:", admin_data["user"]["role"])

        # 3. Login Teacher
        t_res = await client.post("/api/v1/auth/login", json={"username": "teacher1", "password": "Teacher@2024"})
        assert t_res.status_code == 200, f"Teacher login failed: {t_res.text}"
        t_data = t_res.json()
        t_token = t_data["access_token"]
        t_id = t_data["user"]["id"]
        print("[PASS] 3. Teacher Login: OK -> Teacher ID:", t_id)

        # 4. Login Student
        s_res = await client.post("/api/v1/auth/login", json={"username": "student1", "password": "Student@2024"})
        assert s_res.status_code == 200, f"Student login failed: {s_res.text}"
        s_data = s_res.json()
        s_token = s_data["access_token"]
        s_id = s_data["user"]["id"]
        print("[PASS] 4. Student Login: OK -> Student ID:", s_id)

        # 5. Student Dashboard
        headers = {"Authorization": f"Bearer {s_token}"}
        dash_res = await client.get(f"/api/v1/students/{s_id}/dashboard", headers=headers)
        assert dash_res.status_code == 200, f"Student dash failed: {dash_res.text}"
        print("[PASS] 5. Student Dashboard: OK -> Enrolled Subjects:", len(dash_res.json()["enrolled_subjects"]))

        # 6. Student Learn Active Lesson
        learn_res = await client.get(f"/api/v1/students/{s_id}/learn/active?lang=en", headers=headers)
        assert learn_res.status_code == 200, f"Learn failed: {learn_res.text}"
        learn_data = learn_res.json()
        print("[PASS] 6. Student Learn: OK -> Concept:", learn_data["concept_name"], "| Styles:", list(learn_data["styles"].keys()))

        # 7. Student Solve Next Question
        solve_res = await client.get(f"/api/v1/students/{s_id}/solve/next?lang=en", headers=headers)
        assert solve_res.status_code == 200, f"Solve next failed: {solve_res.text}"
        solve_data = solve_res.json()
        q_id = solve_data["question"]["id"]
        print("[PASS] 7. Student Solve Next: OK -> Question ID:", q_id, "| Difficulty:", solve_data["question"]["difficulty_label"])

        # 8. Student Solve Submit
        submit_res = await client.post(f"/api/v1/students/{s_id}/solve/submit", json={
            "question_id": q_id,
            "selected_option": 1,
            "hints_used": 0,
        }, headers=headers)
        assert submit_res.status_code == 200, f"Solve submit failed: {submit_res.text}"
        sub_data = submit_res.json()
        print("[PASS] 8. Student Solve Submit: OK -> Correct?:", sub_data["is_correct"], "| New P(L):", sub_data["new_p_know"])

        # 9. Student Test Paper Generation
        test_res = await client.get(f"/api/v1/students/{s_id}/test/active?lang=en", headers=headers)
        assert test_res.status_code == 200, f"Test active failed: {test_res.text}"
        test_data = test_res.json()
        print("[PASS] 9. Student Test Active: OK -> Title:", test_data["title"], "| Total Items:", test_data["total_questions"])

        # 10. Student Test Paper Submission
        test_sub_res = await client.post(f"/api/v1/students/{s_id}/test/submit", json={
            "assessment_id": test_data["assessment_id"],
            "responses": [{"question_id": item["question_id"], "selected_option": 0} for item in test_data["items"][:3]],
        }, headers=headers)
        assert test_sub_res.status_code == 200, f"Test submit failed: {test_sub_res.text}"
        ts_data = test_sub_res.json()
        print("[PASS] 10. Student Test Submit: OK -> Score:", ts_data["score"], "/", ts_data["max_score"], "| Proposal Generated?:", ts_data["proposal_sent_to_teacher"])

        # 11. Teacher Dashboard & Review Queue
        t_headers = {"Authorization": f"Bearer {t_token}"}
        tdash_res = await client.get(f"/api/v1/teachers/{t_id}/dashboard", headers=t_headers)
        assert tdash_res.status_code == 200, f"Teacher dash failed: {tdash_res.text}"
        print("[PASS] 11. Teacher Dashboard: OK -> Pending Reviews:", tdash_res.json()["pending_proposals"])

        rev_res = await client.get(f"/api/v1/teachers/{t_id}/review-queue", headers=t_headers)
        assert rev_res.status_code == 200, f"Review queue failed: {rev_res.text}"
        print("[PASS] 12. Teacher Review Queue: OK -> Queue Count:", len(rev_res.json()))

        # 13. Curriculum List
        curr_res = await client.get("/api/v1/curriculum/subjects", headers=headers)
        assert curr_res.status_code == 200, f"Curriculum failed: {curr_res.text}"
        print("[PASS] 13. Curriculum Subjects: OK -> Total Subjects:", len(curr_res.json()))

        # 14. Parent Login, Children List & Child Progress
        p_res = await client.post("/api/v1/auth/login", json={"username": "parent1", "password": "Parent@2024"})
        assert p_res.status_code == 200, f"Parent login failed: {p_res.text}"
        p_data = p_res.json()
        p_token = p_data["access_token"]
        p_id = p_data["user"]["id"]
        p_headers = {"Authorization": f"Bearer {p_token}"}
        print("[PASS] 14. Parent Login: OK -> Parent ID:", p_id)

        children_res = await client.get(f"/api/v1/parents/{p_id}/children", headers=p_headers)
        assert children_res.status_code == 200, f"Children failed: {children_res.text}"
        children = children_res.json()
        assert len(children) > 0, "No children found for parent"
        print("[PASS] 15. Parent Children List: OK -> Linked Child:", children[0]["name"], "| Relationship:", children[0]["relationship"])

        child_id = children[0]["student_id"]
        prog_res = await client.get(f"/api/v1/parents/{p_id}/children/{child_id}/progress", headers=p_headers)
        assert prog_res.status_code == 200, f"Progress failed: {prog_res.text}"
        prog_data = prog_res.json()
        print("[PASS] 16. Parent Child Progress: OK -> Child Mastery:", prog_data["overall_mastery_pct"], "%")

    print("=" * 60)
    print("SUCCESS: ALL 16 END-TO-END INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
