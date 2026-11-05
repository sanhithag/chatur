import asyncio
import httpx
from app.main import app

async def test_tasks():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        l = await client.post('/api/v1/auth/login', json={'username': 'student1', 'password': 'Student@2024'})
        assert l.status_code == 200, l.text
        tok = l.json()['access_token']
        uid = l.json()['user']['id']
        headers = {'Authorization': f'Bearer {tok}'}

        # Create Task
        t1 = await client.post(f'/api/v1/students/{uid}/tasks', json={'title': 'Read Ch 1 Physics', 'task_type': 'lesson'}, headers=headers)
        assert t1.status_code == 201, t1.text
        tid = t1.json()['id']
        print('[PASS] Created Task:', t1.json()['title'])

        # List Tasks
        glist = await client.get(f'/api/v1/students/{uid}/tasks', headers=headers)
        assert len(glist.json()) > 0
        print(f'[PASS] Listed Tasks: {len(glist.json())} item(s)')

        # Complete Task
        pup = await client.patch(f'/api/v1/students/{uid}/tasks/{tid}', json={'is_completed': True}, headers=headers)
        assert pup.json()['is_completed'] is True
        print('[PASS] Completed Task:', pup.json()['is_completed'])

        # Delete Task
        d = await client.delete(f'/api/v1/students/{uid}/tasks/{tid}', headers=headers)
        assert d.status_code in (200, 204), d.text
        print('[PASS] Deleted Task successfully')

if __name__ == '__main__':
    asyncio.run(test_tasks())
