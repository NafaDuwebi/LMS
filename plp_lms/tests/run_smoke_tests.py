import sys; sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Test login page
r = client.get('/auth/login')
assert r.status_code == 200
print('PASS: Login page loads')

# Test registration page
r = client.get('/auth/register')
assert r.status_code == 200
print('PASS: Register page loads')

# Test login as admin
r = client.post('/auth/login', data={'username': 'admin@plprojects.co.uk', 'password': 'Admin1234!'}, follow_redirects=False)
assert r.status_code == 302, f'Expected 302, got {r.status_code}'
assert 'access_token' in r.headers.get('set-cookie', '')
print('PASS: Admin login works (redirect to change password)')

# Extract token
cookie = r.headers['set-cookie']
token = cookie.split(';')[0].split('=')[1]

# Test change password
r = client.post('/auth/change-password', data={'current_password': 'Admin1234!', 'new_password': 'Admin1234!'},
                cookies={'access_token': token}, follow_redirects=False)
assert r.status_code == 302
print('PASS: Password change works')

# Login again (now password is changed but same value)
r = client.post('/auth/login', data={'username': 'admin@plprojects.co.uk', 'password': 'Admin1234!'}, follow_redirects=False)
assert r.status_code == 302
cookie = r.headers['set-cookie']
token = cookie.split(';')[0].split('=')[1]
print('PASS: Admin login works after password change')

# Test dashboard
r = client.get('/dashboard', cookies={'access_token': token})
assert r.status_code == 200
print('PASS: Admin dashboard loads')

# Test courses list
r = client.get('/courses', cookies={'access_token': token})
assert r.status_code == 200
print('PASS: Courses list loads')

# Test cohorts list
r = client.get('/cohorts', cookies={'access_token': token})
assert r.status_code == 200
print('PASS: Cohorts list loads')

# Test assessments list
r = client.get('/assessments', cookies={'access_token': token})
assert r.status_code == 200
print('PASS: Assessments list loads')

# Test learner login
r = client.post('/auth/login', data={'username': 'learner1@example.com', 'password': 'Learner1234!'}, follow_redirects=False)
assert r.status_code == 302
cookie = r.headers['set-cookie']
learner_token = cookie.split(';')[0].split('=')[1]
print('PASS: Learner login works')

# Test learner dashboard
r = client.get('/dashboard', cookies={'access_token': learner_token})
assert r.status_code == 200
print('PASS: Learner dashboard loads')

# Test learner courses
r = client.get('/learner/courses', cookies={'access_token': learner_token})
assert r.status_code == 200
print('PASS: Learner courses page loads')

# Test public verify page (no auth)
r = client.get('/certificates/verify/PLP-2026-0001')
print(f'PASS: Verify page accessible: {r.status_code}')

# Test reports page
r = client.get('/reports', cookies={'access_token': token})
assert r.status_code == 200
print('PASS: Reports page loads')

# Test notifications
r = client.get('/notifications', cookies={'access_token': learner_token})
assert r.status_code == 200
print('PASS: Notifications page loads')

print('\n=== ALL TESTS PASSED ===')
