# PLP LMS — Playwright E2E Tests

## Setup

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

Ensure the server is running on port 8001:
```bash
cd plp_lms
python seed_data.py
uvicorn main:app --host 127.0.0.1 --port 8001
```

## Run Tests

```bash
# Headless (CI mode)
npx playwright test --reporter=list

# Headed (watch browser)
npx playwright test --headed --reporter=list

# Debug mode
npx playwright test --debug
```

## Test Structure

| File | Coverage |
|------|----------|
| `auth.spec.js` | Login, logout, registration, error handling for all 4 roles |
| `admin.spec.js` | Dashboard, user CRUD, course CRUD, cohort enrolment, settings, audit log |
| `learner.spec.js` | Dashboard, my courses, course view, assessment take, training record CRUD, profile, notifications, messages |
| `trainer.spec.js` | Dashboard, my cohorts, learners, submissions, marking queue, attendance |
| `certificates.spec.js` | Certificate list, public verify page |
| `observer.spec.js` | Dashboard, courses, cohorts, reports (read-only) |
| `reports.spec.js` | Cohort summary, cert register, compliance (JSON + CSV) |
| `v2_features.spec.js` | Learning paths, skills, documents, RPL, retention, subscriptions |
| `gdpr.spec.js` | GDPR export ZIP download, retention review |
