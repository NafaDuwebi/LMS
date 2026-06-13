import sys; sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

r = client.get('/auth/login')
print(f'Login page: {r.status_code} ({len(r.text)} chars)')

r2 = client.post('/auth/login', data={'username': 'admin@plprojects.co.uk', 'password': 'Admin1234!'}, follow_redirects=False)
print(f'Login POST: {r2.status_code}')
if 'set-cookie' in r2.headers:
    print(f'Set-Cookie: {r2.headers["set-cookie"][:80]}...')
else:
    print('No set-cookie header')

r3 = client.get('/dashboard', cookies={'access_token': 'test'}, follow_redirects=False)
print(f'Dashboard unauthed: {r3.status_code}')
print('All OK')
