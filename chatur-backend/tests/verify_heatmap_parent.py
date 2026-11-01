"""Targeted test to verify Teacher Heatmap and Parent Dashboard progress."""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import ASGITransport, AsyncClient
from app.main import app


async def test_heatmap_and_parent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as teacher1
        t_res = await client.post("/api/v1/auth/login", json={"username": "teacher1", "password": "Teacher@2024"})
        assert t_res.status_code == 200, f"Teacher login failed: {t_res.text}"
        t_data = t_res.json()
        teacher_id = t_data["user"]["id"]
        t_headers = {"Authorization": f"Bearer {t_data['access_token']}"}

        # 2. Get Teacher Heatmap
        hm_res = await client.get(f"/api/v1/teachers/{teacher_id}/heatmap", headers=t_headers)
        assert hm_res.status_code == 200, f"Heatmap failed: {hm_res.text}"
        hm_data = hm_res.json()
        assert "concepts" in hm_data, f"Missing 'concepts' in heatmap response: {hm_data.keys()}"
        assert "students" in hm_data, f"Missing 'students' in heatmap response: {hm_data.keys()}"
        print(f"[PASS] Heatmap returned {len(hm_data['concepts'])} concepts and {len(hm_data['students'])} students.")
        for s in hm_data["students"]:
            print(f"  Student: {s['student_name']} -> {len(s['mastery'])} concept masteries loaded")
            assert len(s["mastery"]) > 0, f"No mastery data for student {s['student_name']}"

        # 3. Login as parent1
        p_res = await client.post("/api/v1/auth/login", json={"username": "parent1", "password": "Parent@2024"})
        assert p_res.status_code == 200, f"Parent login failed: {p_res.text}"
        p_data = p_res.json()
        parent_id = p_data["user"]["id"]
        p_headers = {"Authorization": f"Bearer {p_data['access_token']}"}

        # 4. Get Parent Children
        c_res = await client.get(f"/api/v1/parents/{parent_id}/children", headers=p_headers)
        assert c_res.status_code == 200, f"Parent children failed: {c_res.text}"
        children = c_res.json()
        assert len(children) > 0, "No children returned for parent"
        child = children[0]
        print(f"\n[PASS] Parent children returned {len(children)} child(ren):")
        print(f"  Child Name: {child.get('student_name') or child.get('name')} | ID: {child['student_id']} | Grade: {child['grade']}{child['section']}")

        # 5. Get Child Progress
        prog_res = await client.get(f"/api/v1/parents/{parent_id}/children/{child['student_id']}/progress", headers=p_headers)
        assert prog_res.status_code == 200, f"Child progress failed: {prog_res.text}"
        prog = prog_res.json()
        assert "concept_progress" in prog or "concepts" in prog, "No concept progress found"
        concepts = prog.get("concept_progress") or prog.get("concepts")
        print(f"\n[PASS] Child Progress loaded successfully:")
        print(f"  Student: {prog['student_name']} | Overall Mastery: {prog['overall_mastery_pct']}% | Total XP: {prog['total_xp']}")
        print(f"  Concepts tracked: {len(concepts)}")
        for cp in concepts[:3]:
            c_name = cp.get("concept_name") or cp.get("name")
            p_val = cp.get("p_know")
            on_track = cp.get("on_track")
            print(f"    - {c_name}: {round(p_val * 100)}% (On Track: {on_track})")

    print("\n" + "=" * 60)
    print("ALL HEATMAP AND PARENT DASHBOARD VERIFICATIONS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_heatmap_and_parent())
