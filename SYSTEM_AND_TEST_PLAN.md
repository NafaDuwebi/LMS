# PLP Learning Management System — System Architecture & Test Plan

---

## 1. System Architecture

### 1.1 Overview

PLP LMS is a **desktop/local-web Learning Management System** built for PL Projects Ltd, a UK-based B Corp certified project management consultancy. It delivers APM-accredited courses (PFQ, PMQ), risk management, and CITB awareness training through a role-based portal.

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite via SQLAlchemy ORM |
| Auth | bcrypt password hashing, JWT (HS256) in HTTP-only cookies |
| Frontend | Server-rendered Jinja2 templates + TailwindCSS (CDN) |
| PDF | ReportLab for certificate generation |
| Charts | Plotly for progress/analytics |
| File Storage | Local filesystem (`uploads/`, `certificates/`, `exports/`) |
| Email | SMTP via `smtplib` (Office365 default) |

### 1.2 Directory Structure

```
plp_lms/
├── main.py                  # FastAPI app entry, mounts static/uploads, includes routers
├── config.py                # Env-based config (SMTP, JWT, upload limits, org settings)
├── database.py              # SQLAlchemy engine, session factory, Base, init_db()
├── models/                  # 17 SQLAlchemy ORM models (one file per domain)
│   ├── user.py              # User (5 roles: superadmin, trainer, learner, observer)
│   ├── course.py            # Course, LearningOutcome, Module, Material
│   ├── cohort.py            # Cohort, Enrolment, AttendanceRecord
│   ├── assessment.py        # Assessment, Question, AnswerOption, QuestionBank
│   ├── submission.py        # Submission, Answer
│   ├── certificate.py       # Certificate
│   ├── training_record.py   # TrainingRecord
│   ├── notification.py      # Notification
│   ├── audit.py             # AuditLog
│   ├── learning_path.py     # LearningPath, LearningPathCourse, LearningPathEnrolment
│   ├── skill.py             # Skill, SkillClaim
│   ├── document.py          # EnrolmentDocumentRequirement, EnrolmentDocumentSubmission
│   ├── message.py           # Message
│   ├── rpl.py               # RplClaim
│   ├── report_subscription.py # ReportSubscription
│   └── retention.py         # RetentionLog
├── routers/                 # 14 FastAPI route modules
│   ├── auth.py              # Login, register, self-enrol via token, change password
│   ├── dashboard.py         # Role-routed dashboards (admin/trainer/learner/observer)
│   ├── admin.py             # User CRUD, settings, audit log, GDPR export
│   ├── trainer.py           # My cohorts, learners, pending submissions
│   ├── learner.py           # My courses, course view, profile, training record, results, certificates
│   ├── courses.py           # Course/Module/Material CRUD with file upload
│   ├── cohorts.py           # Cohort CRUD, enrol by email, bulk CSV import
│   ├── assessments.py       # Assessment CRUD, take, submit, auto-mark MCQ, marking queue
│   ├── attendance.py        # Session register, add session, record/delete attendance
│   ├── certificates.py      # Issue, revoke, download certificates, public verify
│   ├── reports.py           # Cohort summary, learner progress, cert register, compliance (JSON/CSV)
│   ├── notifications.py     # List, mark-read, mark-all-read, unread count
│   └── v2_1.py              # All v2.1 improvements (learning paths, skills, docs, messages, RPL, retention, subscriptions)
├── services/                # 7 business-logic modules
│   ├── auth_service.py      # Password hashing, JWT create/decode, get_current_user, require_role, lockout
│   ├── certificate_service.py # PDF generation via ReportLab, cert number, revoke
│   ├── notification_service.py # Create/mark-read notifications, enrolment/result/cert helpers
│   ├── progress_service.py  # Module-by-module learner progress, cohort summary
│   ├── report_service.py    # CSV generation, cohort/learner/cert/compliance reports
│   ├── email_service.py     # SMTP send, also writes to messages table as fallback
│   └── bulk_import_service.py # CSV bulk enrol with auto-user-creation
├── templates/               # 41+ Jinja2 templates
│   ├── base.html / layout.html
│   ├── auth/                # login.html, register.html, change_password.html
│   ├── admin/               # dashboard, users, user_form, settings, audit_log
│   ├── trainer/             # dashboard, cohorts, learners, submissions
│   ├── learner/             # dashboard, my_courses, course_view, profile, training_record, results, certificates
│   ├── shared/              # courses, cohorts, assessments, marking, attendance, reports, notifications, certificates, observer_dashboard
│   └── v2/                  # v2.1 features (learning paths, skills, documents, messages, RPL, retention, subscriptions)
├── seed_data.py             # 5 default users, 5 courses, 1 cohort, 1 assessment, 5 questions
├── migrate_v2_1.py          # DB migration for v2.1 improvements (safe re-run, no table drops)
├── start_lms.bat            # Desktop launcher shortcut
├── requirements.txt         # Python dependencies
└── PLP_LMS_User_Guide.md    # User guide
```

### 1.3 Request Flow

```
Browser → FastAPI (uvicorn) → Router → (auth middleware) → Service Layer → SQLAlchemy → SQLite
                                            ↓
                                     Jinja2 Template → HTML Response
```

- **Auth middleware** (`get_current_user` / `require_role`) validates the JWT from the `access_token` cookie on every request.
- **Role-based access** enforced at the router level via `dependencies=[Depends(require_role("superadmin"))]` or checked inline in handler logic.
- **All pages** are server-rendered Jinja2 templates (no SPA framework).

### 1.4 Database Design (17 Models)

| Model | Key Fields | Relationships |
|-------|-----------|---------------|
| User | id, username, email, password_hash, role, is_active, force_password_change, gdpr_consent_date, failed_login_attempts, locked_until | enrolments, certificates, training_records, notifications |
| Course | id, course_code, title, awarding_body, level, pass_mark, assessment_type, delivery_mode, cert_validity_years, prerequisites | modules, learning_outcomes, cohorts, assessments, certificates |
| Module | id, course_id, title, order_index, is_published, delivery_mode | course, materials |
| Material | id, module_id, title, file_type, file_path, file_size_kb, url | module |
| Cohort | id, name, course_id, trainer_id, start_date, end_date, max_learners, enrolment_token, is_active, delivery_mode, venue | course, trainer, enrolments, attendance_records |
| Enrolment | id, user_id, cohort_id, status, final_score, retention_review_date, retention_status | cohort, user, attendance_records |
| AttendanceRecord | id, enrolment_id, cohort_id, session_date, attended, notes | enrolment, cohort, recorder |
| Assessment | id, course_id, module_id, title, type (mcq/written/practical), max_attempts, pass_mark, time_limit_mins, is_published, randomise_* | course, questions, submissions |
| Question | id, assessment_id, question_text, question_type, marks, order_index | assessment, answer_options, answers |
| AnswerOption | id, question_id, option_text, is_correct | question |
| Submission | id, user_id, assessment_id, attempt_number, score, passed, status, feedback | user, assessment, answers |
| Answer | id, submission_id, question_id, answer_text, selected_option_id, marks_awarded | submission, question |
| Certificate | id, user_id, course_id, enrolment_id, certificate_number, pdf_path, issued_at, expiry_date, revoked | user, course |
| TrainingRecord | id, user_id, record_type, title, provider, completion_date, hours, evidence_path | user, verifier |
| Notification | id, user_id, type, title, message, is_read, action_url | user |
| AuditLog | id, user_id, action, target_type, target_id, ip_address, notes | user |
| LearningPath | id, title, description, is_published, created_by | courses (through LPC), enrolments (through LPE) |
| LearningPathCourse | id, path_id, course_id, order_index, unlock_on_previous | path, course |
| LearningPathEnrolment | id, user_id, path_id, enrolled_at, completed_at, status | path, user |
| Skill | id, title, description, how_to_demonstrate, course_id, created_by | claims |
| SkillClaim | id, skill_id, user_id, reviewer_id, claim_comment, evidence_path, status | skill, user, reviewer |
| EnrolmentDocumentRequirement | id, cohort_id, document_label, instructions, is_required | cohort, submissions |
| EnrolmentDocumentSubmission | id, requirement_id, user_id, file_path, status, reviewed_by | requirement, user, reviewer |
| Message | id, user_id, subject, body_html, triggered_by, is_read, read_at | user |
| RplClaim | id, user_id, course_id, prior_title, prior_provider, evidence_path, status, reviewed_by | user, course, reviewer |
| ReportSubscription | id, report_id, created_by, recipient_emails (JSON), frequency, day_of_week, day_of_month, send_time, is_active | user |
| RetentionLog | id, user_id, action, actioned_by, notes | user |

### 1.5 Authentication & Security

- **Password hashing**: bcrypt via passlib (bcrypt==4.1.2 pinned).
- **JWT tokens**: HS256 with 480-minute (8-hour) expiry, stored in HTTP-only cookie `access_token`.
- **Account lockout**: 5 failed attempts triggers a 30-minute lock.
- **Force password change**: On first login (admin-created users) or when triggered by admin.
- **Self-registration**: Sets `is_active=False` — requires admin approval before login.
- **GDPR**: Consent date recorded on registration, Subject Access Request export available.

### 1.6 Key Services

| Service | Responsibility |
|---------|---------------|
| `auth_service.py` | Hash/verify passwords, JWT create/decode, current-user extraction, role enforcement, lockout logic |
| `certificate_service.py` | Generate PDF certificates via ReportLab with PLP branding, unique cert numbers, expiry computation |
| `notification_service.py` | Create notifications, mark read/unread, helper functions for enrolment/result/cert notifications |
| `progress_service.py` | Module-by-module completion tracking, cohort-level progress summary |
| `report_service.py` | Generate structured data for cohort summary, learner progress, certificate register, compliance reports; CSV export |
| `email_service.py` | SMTP email sending (welcome, certificate, reminders); also writes to `messages` table |
| `bulk_import_service.py` | Parse CSV, create users if needed, enrol in cohort, send welcome emails |

---

## 2. User Roles & Functionality

### 2.1 Super Admin (`admin@plprojects.co.uk`)

**Access**: All system features. Router-level `require_role("superadmin")`.

Capabilities:
- **Dashboard**: Aggregate stats (total learners, trainers, active cohorts, pending marking, expiring certs).
- **User Management**: Create/edit/list/delete users, approve pending registrations, set roles, force password change.
- **Course Management**: Create/edit/delete courses, modules, materials, learning outcomes, reorder modules.
- **Cohort Management**: Create/edit/delete cohorts, set trainer, enrol by email, bulk CSV import, enrolment token management.
- **Assessment Management**: Create/edit/delete assessments and questions (MCQ/written/practical), view all submissions.
- **Marking Queue**: Mark written assessment submissions, overall feedback.
- **Attendance**: View and record attendance for any cohort.
- **Certificates**: Issue and revoke certificates, download, public verification.
- **Reports**: Cohort summary, learner progress, certificate register, compliance (JSON/CSV).
- **Settings**: Configure org name, attendance threshold, data retention years, max upload size.
- **Audit Log**: View 100 most recent audit log entries.
- **GDPR Export**: Download user data as ZIP.
- **Notifications**: In-app notification centre.
- **v2.1 Features**: Learning paths (CRUD), skills management, document requirements, messages, RPL review, retention review, report subscriptions.

### 2.2 Trainer (`trainer@plprojects.co.uk`)

**Access**: Router-level `require_role("trainer", "superadmin")`.

Capabilities:
- **Dashboard**: My cohorts count, pending marking count, upcoming sessions.
- **My Cohorts**: List of cohorts assigned (via `trainer_id`), view learners, update enrolment status.
- **My Learners**: All learners enrolled in assigned cohorts.
- **Pending Submissions**: Written assessments awaiting marking for their courses.
- **Assessments**: View assessments for their courses, view marking queue.
- **Attendance**: Record and manage session attendance for their cohorts.
- **Certificates**: List certificates for their courses.
- **Courses**: View course structure.
- **Learning Paths**: View (admin manages).
- **Skills**: View skills, review skill claims (shared queue).
- **Documents**: Review submitted enrolment documents.
- **RPL**: Review Recognition of Prior Learning claims.

### 2.3 Learner (`learner1@example.com`, `learner2@example.com`)

**Access**: No role restriction beyond `get_current_user`.

Capabilities:
- **Dashboard**: My enrolments, recent notifications.
- **My Courses**: List of enrolled courses with progress %, per-module status.
- **Course View**: Per-course module-by-module view, download materials, take assessments.
- **Profile**: Edit personal details, change password.
- **Training Record**: View completed courses, certificates, and external training records. Add/edit/delete external training.
- **Results**: View released assessment scores.
- **Certificates**: View/download issued certificates.
- **Notifications**: In-app notification centre.
- **Learning Paths**: Enrol in paths, auto-enrol in first course cohort.
- **Skills**: View skills, submit skill claims with evidence, view claim status.
- **Documents**: Upload enrolment documents for cohort requirements.
- **Messages**: View system messages (email fallback).
- **RPL**: Submit Recognition of Prior Learning claims.

### 2.4 Observer (`observer@plprojects.co.uk`)

**Access**: No role restriction beyond `get_current_user`.

Capabilities:
- **Dashboard**: Overview of all active cohorts.
- **View-only**: Can see courses, cohorts (read-only), reports.

---

## 3. Detailed Test Plan

### 3.1 End-to-End Test Scenarios — Critical User Journeys

#### EUJ-1: Complete Admin Course Lifecycle
1. Admin logs in (changes password on first login).
2. Admin creates a new course with modules and materials.
3. Admin adds learning outcomes.
4. Admin creates an assessment with MCQ questions.
5. Admin creates a cohort linked to the course and trainer.
6. Admin enrols a learner by email (auto-creates user if needed).
7. Admin bulk-imports learners via CSV.
8. Admin views the cohort, updates enrolment status.
9. Admin creates a learning path containing the course.

#### EUJ-2: Complete Learner Journey
1. Learner self-registers (sets `is_active=False`).
2. Admin approves the registration.
3. Learner logs in, changes password if forced.
4. Learner views enrolled course in My Courses.
5. Learner opens a course, views modules and materials.
6. Learner downloads a material.
7. Learner takes an MCQ assessment, receives auto-graded result.
8. Learner views results page.
9. Learner views/downloads certificate (if issued).
10. Learner adds, edits, and deletes external training records.
11. Learner views profile, updates details, changes password.

#### EUJ-3: Trainer Assessment Marking
1. Learner takes a written assessment (submitted status).
2. Trainer views pending submissions on dashboard.
3. Trainer opens marking queue.
4. Trainer marks each question, provides feedback.
5. Trainer releases results.
6. Learner receives notification and views scored result.

#### EUJ-4: Attendance Workflow
1. Trainer adds a session date to a cohort.
2. Trainer marks attendance (present/absent with notes).
3. Attendance records persist and display correctly.
4. Trainer deletes a session.

#### EUJ-5: Certificate Lifecycle
1. Learner completes a course (status = completed).
2. Admin issues certificate.
3. Certificate PDF is generated and downloadable.
4. Learner views certificate in their list.
5. Public verifies certificate via `/verify/{cert_number}`.
6. Admin revokes certificate with reason.
7. Verification shows revoked status.

#### EUJ-6: Skill Sign-off (v2.1)
1. Admin/trainer creates a skill for a course.
2. Learner submits a skill claim with evidence upload.
3. Admin/trainer reviews the claim in the review queue.
4. Claim is approved/rejected with comment.
5. Learner sees updated claim status.

#### EUJ-7: Document Requirements (v2.1)
1. Admin adds document requirement to a cohort.
2. Learner uploads a document file.
3. Admin reviews document (approve/reject).
4. Submission status updates.

#### EUJ-8: RPL Claim (v2.1)
1. Learner submits RPL claim for a course with evidence.
2. Admin reviews and approves claim.
3. Enrolment auto-created and marked completed.
4. Learner sees the completion in training record.

#### EUJ-9: GDPR Retention (v2.1)
1. Admin views flagged enrolments past retention date.
2. Admin anonymises a learner record.
3. Admin extends retention period.
4. Retention log records the action.

#### EUJ-10: Report Subscriptions (v2.1)
1. Admin creates a scheduled report subscription.
2. Admin toggles subscription active/inactive.
3. Admin deletes a subscription.

#### EUJ-11: Notifications & Messages (v2.1)
1. System generates notifications on enrolment, result, cert issue, skill claim.
2. Learner views notifications, marks as read, marks all read.
3. System writes messages table when email is sent.
4. Learner views messages centre.

#### EUJ-12: Account Lockout & Security
1. Admin attempts login with wrong password 5 times.
2. Account is locked for 30 minutes.
3. Admin cannot log in during lockout.
4. After lockout expiry (or DB reset), login succeeds.
5. Force password change redirects user on next login.

### 3.2 Integration Test Points

| Component | Integration Point | Verification |
|-----------|------------------|--------------|
| Email | `email_service.py` → SMTP | Email sent (or written to `messages` table) |
| Email → Messages | `send_email()` with `user_id` + `db` | Message record created in DB |
| File Upload | Material create, skill claim, doc upload, RPL | File saved to `uploads/` with correct path in DB |
| Certificate PDF | `certificate_service.py` → ReportLab | PDF file created at expected path, content valid |
| Bulk CSV | File upload → `bulk_import_service.py` | Users created, enrolments added, welcome emails sent |
| Auth JWT | Login → cookie → subsequent requests | Token decoded, user extracted, role checked |
| Notification | `create_notification()` across all call sites | Notification record created in DB |
| Audit Log | All mutation actions | AuditLog record created for create/update/delete/approve/reject actions |
| Report CSV | `reports/` endpoints with `format=csv` | CSV file response with correct headers and data |
| GDPR Export | `/admin/gdpr-export/{id}` | ZIP file containing JSON of user data |

### 3.3 Functional Test Checklist

#### Authentication
- [ ] Login page loads at `/auth/login`
- [ ] Register page loads at `/auth/register`
- [ ] Login with valid credentials redirects to dashboard
- [ ] Login with invalid credentials shows error message
- [ ] Login with pending-approval account shows pending message
- [ ] Account locks after 5 failed attempts
- [ ] Force password change redirects user
- [ ] Logout clears token and redirects
- [ ] Registration creates inactive user, notifies admin
- [ ] Self-registration with valid token auto-enrols in cohort
- [ ] Duplicate email/username registration rejected

#### Admin — User Management
- [ ] List all users
- [ ] Create user with all roles
- [ ] Edit user — change role, active status, password, username
- [ ] Approve pending registration
- [ ] Delete non-superadmin user
- [ ] Force password change on user

#### Admin — Courses
- [ ] Create course with all fields
- [ ] Edit course
- [ ] Delete course
- [ ] View course with modules/outcomes
- [ ] Add learning outcome
- [ ] Delete learning outcome

#### Admin — Modules & Materials
- [ ] Create module within course
- [ ] Edit module
- [ ] Delete module
- [ ] Reorder modules (up/down)
- [ ] Upload material file to module
- [ ] Delete material
- [ ] Download material

#### Admin — Cohorts
- [ ] Create cohort with course, trainer, dates
- [ ] Edit cohort
- [ ] Delete cohort
- [ ] View cohort with enrolment stats
- [ ] Enrol learner by email (existing user)
- [ ] Enrol learner by email (new user, auto-created)
- [ ] Bulk import via CSV
- [ ] Update enrolment status
- [ ] Enrolment token displayed

#### Admin — Assessments
- [ ] Create assessment (MCQ/written/practical)
- [ ] Edit assessment
- [ ] Delete assessment
- [ ] Add MCQ question with 4 options, correct answer
- [ ] Delete question
- [ ] View assessment submissions
- [ ] View marking queue

#### Admin — Certificates
- [ ] Issue certificate for completed enrolment
- [ ] Prevent duplicate certificate issue
- [ ] Revoke certificate with reason
- [ ] Public certificate verify page (valid)
- [ ] Public certificate verify page (revoked)
- [ ] Certificate PDF download

#### Admin — Settings
- [ ] View settings page
- [ ] Update org name, attendance threshold, retention, upload limit
- [ ] Settings persisted to .env file

#### Admin — v2.1 Features
- [ ] Create learning path
- [ ] Add/remove course from learning path
- [ ] Create skill
- [ ] Review skill claim (approve/reject)
- [ ] Add document requirement to cohort
- [ ] Review document submission (approve/reject)
- [ ] Review RPL claim (approve → auto-complete)
- [ ] View retention review page
- [ ] Anonymise flagged enrolment
- [ ] Extend retention period
- [ ] Create report subscription
- [ ] Toggle subscription active/inactive
- [ ] Delete subscription
- [ ] View audit log (100 entries)

#### Trainer
- [ ] View assigned cohorts list
- [ ] View learners in cohorts
- [ ] View pending submissions
- [ ] Mark submission (award marks per question, feedback)
- [ ] Add session date → attendance register appears
- [ ] Record attendance (present/absent with notes)
- [ ] Delete session
- [ ] View certificate list for courses

#### Learner
- [ ] Dashboard shows enrolments and notifications
- [ ] My Courses shows enrolled courses with progress %
- [ ] Course view shows modules, materials, assessments
- [ ] Download material file
- [ ] Take MCQ assessment → auto-graded result
- [ ] View results page (released submissions only)
- [ ] View own certificates (download PDF)
- [ ] View training record (completed courses, certs, external)
- [ ] Add external training record
- [ ] Edit external training record
- [ ] Delete external training record
- [ ] View/edit profile (name, org, job title, phone)
- [ ] Change password
- [ ] View notifications (mark read)
- [ ] View messages
- [ ] Enrol in learning path → auto-enrolled in first cohort
- [ ] Submit skill claim with evidence
- [ ] View skill claim status
- [ ] Upload enrolment document
- [ ] Submit RPL claim with evidence

#### Observer
- [ ] Dashboard shows all active cohorts
- [ ] Can browse courses and cohorts (read-only)

#### Reports
- [ ] Reports page loads
- [ ] Cohort summary report (JSON)
- [ ] Cohort summary report (CSV download)
- [ ] Learner progress report
- [ ] Certificate register report
- [ ] Compliance report (JSON)
- [ ] Compliance report (CSV download)

#### GDPR
- [ ] Subject Access Request export (ZIP download)
- [ ] Export contains user data, enrolments, submissions, certificates, training records

#### Notifications
- [ ] Unread count badge on all pages
- [ ] Notifications list page
- [ ] Mark single notification as read
- [ ] Mark all notifications as read

#### Error Handling
- [ ] 404 page for missing resources
- [ ] 403 for unauthorised access
- [ ] Invalid form data returns error message
- [ ] Session expiry redirects to login
- [ ] File upload size validation

---

## 4. Test Environment Setup

### Prerequisites
```bash
cd plp_lms
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
pip install playwright
python seed_data.py
uvicorn main:app --host 127.0.0.1 --port 8001
```

### Running Playwright E2E Tests
```bash
cd tests/e2e
npm install
npx playwright install chromium
npx playwright test --reporter=list
```

### Running Integration Tests (Existing)
```bash
cd plp_lms
python tests/test_all.py
```

---

## 5. Test Data Requirements

| Data | Source |
|------|--------|
| 5 default users (admin, trainer, observer, 2 learners) | `seed_data.py` |
| 5 courses (PFQ, PMQ, RISK-L1, RISK-L2, CITB) | `seed_data.py` |
| PFQ modules (3) with materials (2) | `seed_data.py` |
| 1 MCQ assessment with 5 questions | `seed_data.py` |
| 1 PFQ cohort (2026-A) with 2 learners enrolled | `seed_data.py` |
| Attendance records (3 sessions) | `seed_data.py` |
| Evidence files for skill/RPL claims | Created by tests |
| Bulk import CSV | Created by tests |
