import sys; sys.path.insert(0,'.')
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
# Login as trainer
r = c.post('/auth/login', data={'username':'trainer@plprojects.co.uk','password':'Trainer1234!'}, follow_redirects=False)
t = r.headers['set-cookie'].split(';')[0].split('=')[1]
# Try to enrol a new learner
r = c.post('/cohorts/1/enrol', cookies={'access_token': t}, data={'email': 'newlearner@test.com'}, follow_redirects=False)
print(f'Status: {r.status_code}')
loc = r.headers.get('location', '')
print(f'Location: {loc}')
# Check if user was created... wait, it shouldn't create a user, only enrol an existing one
# Let me check what users exist first
