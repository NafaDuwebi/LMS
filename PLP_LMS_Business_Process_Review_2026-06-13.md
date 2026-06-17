# PLP LMS — Business Process Validation Review
**Date:** 13 June 2026  
**Review Type:** Full 7-Phase Business Process Validation  
**Reviewer Roles:** Senior LMS Consultant · QA Test Manager · Training Manager · Instructional Designer · Learner · System Administrator  
**System:** PLP Learning Management System — FastAPI / SQLAlchemy / PostgreSQL  

---

## PHASE 1 — SYSTEM DISCOVERY

### 1.1 User Roles

| Role | Access Level | Description |
|---|---|---|
| superadmin | Full system | Create/manage users, courses, cohorts, reports, certificates, audit logs, system settings |
| trainer | Course delivery | Manage own cohorts, upload materials, create assessments, mark submissions, issue certificates |
| learner | Enrolled content only | View enrolled courses, take assessments, view results and certificates, log external training |
| observer | Read-only reporting | View cohorts, reports, certificate register, compliance data |
| external_assessor | Skill claims only | Review and approve/reject skill competency claims submitted by learners |

### 1.2 Navigation Structure

**Superadmin routes:**
- `/dashboard` — Stats: learners, trainers, cohorts, pending marking, expiring certs
- `/admin/users` — User management (create, edit, approve, delete)
- `/admin/settings` — Org name, attendance threshold, data retention years, upload limit
- `/admin/audit-log` — Last 100 system actions
- `/admin/gdpr-export/{id}` — Download user data ZIP

**Trainer routes:**
- `/dashboard` — My cohorts, pending marking, upcoming sessions
- `/trainer/cohorts` — Trainer's assigned cohorts
- `/trainer/learners` — Learners across all assigned cohorts
- `/trainer/submissions` — Pending submissions for marking

**Learner routes:**
- `/dashboard` — Enrolled courses with progress, unread notifications
- `/learner/courses` — My courses list with progress bars
- `/learner/course/{id}` — Course view with modules and materials
- `/learner/training-record` — External training log (add/edit/delete)
- `/learner/results` — Released assessment results
- `/learner/certificates` — Issued certificates (download)
- `/learner/profile` — Update profile, change password, request deletion

**Shared routes (role-filtered):**
- `/courses` — Course library (admin: all; trainer: own; learner: published)
- `/cohorts` — Cohort management
- `/assessments` — Assessment bank and marking queue
- `/assessments/{id}/take` — Take an assessment
- `/certificates` — Certificate register
- `/reports` — Reporting suite
- `/attendance` — Attendance register

**V2 routes (advanced features):**
- `/learning-paths` — Sequenced course pathways
- `/skills` / `/skills/claim` — Skill competency claims
- `/rpl` — Recognition of Prior Learning
- `/documents` — Document requirements and submissions
- `/messages` — Internal messaging
- `/admin/retention` — Data retention review

### 1.3 Course Management Process

```
Course (code, title, level, awarding body, pass mark, delivery mode, duration, cert validity)
  └── Module (title, description, order, delivery mode)
        └── Material (title, file: PDF/DOCX/PPTX/MP4/PNG/JPG or URL)
  └── Assessment (type: MCQ/written/mixed, pass mark, max attempts, time limit)
        └── Question (type: MCQ/written, marks)
              └── Answer Options (for MCQ: A/B/C/D with correct flag)
  └── Learning Outcome (text, syllabus area)
  └── Cohort (name, trainer, start/end date, max learners, delivery mode, venue)
        └── Enrolment (user → cohort, status: enrolled/in_progress/completed/dropped)
```

### 1.4 Training Workflow

1. Admin creates course → modules → materials → assessments
2. Admin creates cohort (links course + trainer + dates)
3. Trainer or admin enrols learners (by email, or CSV bulk import, or self-enrolment token)
4. Learner logs in → sees dashboard with enrolled cohorts
5. Learner views course materials → takes assessments
6. MCQ: auto-graded and result shown immediately (if release_results_immediately = True)
7. Written/mixed: submitted → trainer marks → result released
8. Trainer manually marks enrolment as "completed" via cohort view
9. Trainer/admin issues certificate manually via cohort view
10. Learner downloads certificate from profile

### 1.5 Assessment Workflow

| Type | Submission | Grading | Result Release |
|---|---|---|---|
| MCQ | Online form | Automatic | Immediate (if flag set) |
| Written | Text answer | Manual by trainer | Manual release by trainer |
| Mixed | MCQ + text | MCQ auto + written manual | Released when marked |

**Max attempts** enforced per assessment. Attempt tracking by count query.

### 1.6 Reporting Workflow

Reports accessible to superadmin, trainer, and observer:
- **Cohort Summary** — enrolment stats, completion rates, average scores
- **Learner Progress** — individual learner progress per course
- **Certificate Register** — all issued certs with expiry dates
- **Compliance Report** — cert status by learner (CSV export available)

### 1.7 Certification Workflow

1. Learner completes course (enrolment marked "completed" by trainer/admin)
2. Trainer/admin clicks "Issue Certificate" in cohort view (MANUAL step)
3. PDF generated with learner name, course title, cert number, issue/expiry date
4. Learner notified via system notification
5. Learner downloads PDF from `/learner/certificates`
6. Public verification available at `/certificates/verify/{cert_number}` (no login required)

### 1.8 User Management Workflow

1. Learner self-registers → `is_active=False` → awaits admin approval
2. Admin approves → `is_active=True` → approval email sent
3. Admin can also create users directly (force_password_change=True)
4. Admin can bulk enrol via CSV (new users created with setup token + welcome email)
5. Admin can deactivate, edit roles, or delete users (except superadmin)
6. GDPR: export (ZIP), anonymise, data retention flagging (automated via scheduler)

### 1.9 System Summary

The PLP LMS is a **competency-based, cohort-driven learning management system** built for professional/vocational training delivery. It supports course building, blended delivery, MCQ and written assessments, manual and automatic marking, PDF certificate generation, and basic reporting. Advanced features include learning paths, RPL, skill claims, document requirements, and GDPR compliance tools.

**The system is functional for its core purpose** but has significant gaps in learner autonomy, automation, tracking granularity, and administrative controls compared to enterprise LMS platforms.

---

## PHASE 2 — LEARNER JOURNEY REVIEW

### Learner Journey Map

```
REGISTER → LOGIN → GDPR CONSENT → DASHBOARD → FIND COURSE → ACCESS COURSE
    → VIEW MATERIALS → TAKE ASSESSMENT → VIEW RESULT → TRAINER MARKS (if written)
    → COURSE COMPLETE (manual) → CERTIFICATE ISSUED (manual) → DOWNLOAD CERT → VIEW HISTORY
```

---

### Step 1: Register

**Expected:** Learner navigates to `/auth/register`, fills in name, username, email, password, GDPR consent, submits.  
**Actual:** Form works. Validation of password strength (10 chars, upper/lower/digit/special) and GDPR checkbox enforced. Account created with `is_active=False`.  
**Issue:** After registration, learner sees "pending approval" message but has no visibility of wait time or who to contact.  
**Missing:** No estimated approval time, no auto-email to the learner confirming receipt, no self-service approval bypass for pre-vetted learners.  
**Severity:** 🟡 MEDIUM  
**Compliance:** GDPR consent is captured at registration with date stamp. ✓

---

### Step 2: Log In

**Expected:** Enter username or email + password, get redirected to dashboard.  
**Actual:** Works correctly. Account lockout after 5 failed attempts (30-minute lockout). JWT cookie set with httponly + samesite=strict.  
**Issue:** If account is locked, error message says "Account locked. Try again later." but gives no indication of lockout duration or when the user can retry.  
**Missing:** Lockout remaining time in error message.  
**Severity:** 🔵 LOW

---

### Step 3: GDPR Consent

**Expected:** On first login after admin creates account, learner is shown a GDPR consent page and must accept before proceeding.  
**Actual:** `requires_gdpr_consent` flag triggers redirect to `/auth/gdpr-consent`. Works correctly for admin-created accounts.  
**Issue:** A self-registered learner already accepts GDPR at registration, but the `requires_gdpr_consent` flag is not set, so they see the GDPR page again on first admin-created reactivation.  
**Severity:** 🔵 LOW

---

### Step 4: Access Dashboard

**Expected:** Learner sees their enrolled courses, progress indicators, and notifications.  
**Actual:** Dashboard shows enrolled cohorts and unread notifications. Progress is visible per cohort.  
**Issues:**  
- Dashboard shows enrolled cohort names (not course names). Learner sees "Cohort A" not "Health and Safety Level 2". The course title should be prominent.  
- No "Start Learning" call-to-action button directly on the dashboard card.  
- No visual progress bar on dashboard cards — only in `/learner/courses`.  
**Missing:** Upcoming deadlines, overdue assessments, and expiring certificates are not surfaced on the learner dashboard.  
**Severity:** 🟠 HIGH (UX — directly impacts learner engagement and course start rate)

---

### Step 5: View Available Courses

**Expected:** Learner can browse all available courses and choose what to enrol in.  
**Actual:** `/courses` shows published courses to learners, BUT there is **no self-enrolment button**. Learners can see courses but cannot enrol themselves. Enrolment requires a trainer/admin to enrol them, or a token link.  
**Missing:**  
- Course catalogue with self-enrolment option  
- Course search and filtering  
- Course difficulty level display  
- Course preview (description and learning outcomes shown — this is good, but no image/thumbnail)  
**Severity:** 🔴 CRITICAL — A core LMS function. Without self-enrolment, all enrolment is admin-dependent, creating a bottleneck and reducing learner autonomy.

---

### Step 6: Enrol on a Course

**Expected:** Learner clicks "Enrol" and is enrolled in the next available cohort.  
**Actual:** No self-enrolment pathway exists. Learners can use a token link sent by admin (`/auth/join/{token}`) to register and self-enrol in a cohort, but they cannot discover or enrol from within the platform once logged in.  
**Missing:**  
- In-app self-enrolment  
- Enrolment request workflow (learner requests, admin approves)  
- Waiting list for full cohorts  
- Prerequisite checks before enrolment  
**Severity:** 🔴 CRITICAL

---

### Step 7: Start Learning

**Expected:** Learner opens their course, sees modules in order, and accesses learning materials.  
**Actual:** `/learner/course/{id}` shows course structure with modules and materials. Materials can be downloaded (files) or accessed via URL (links).  
**Issues:**  
- **No in-browser material viewing** — PDFs, videos, and documents are download-only. Learner must use their own viewer. Industry standard is an embedded reader/player.  
- **No material completion tracking** — the system has no record of a learner having viewed or downloaded a material. Progress is assessment-only.  
- **No sequential module locking** — all modules are visible and accessible simultaneously. There is no "complete Module 1 before accessing Module 2" enforcement.  
- **No estimated time** shown per module or material.  
**Missing:** In-browser PDF viewer, video player, material completion checkmarks, sequential unlocking.  
**Severity:** 🟠 HIGH (material viewing) · 🟡 MEDIUM (sequential locking)

---

### Step 8: Complete Lessons / Quizzes

**Expected:** Learner completes a lesson (marks it done) and takes a quiz with immediate feedback.  
**Actual:**  
- MCQ assessments can be taken online. Questions are listed in order (or randomised if configured). Learner selects answer and submits.  
- If `release_results_immediately=True` (MCQ default), score is shown immediately.  
- Question-level feedback is not shown on the result page — only overall score and pass/fail.  
**Missing:**  
- **No "lesson complete" concept** — materials have no completion button. Only assessments mark progress.  
- **No per-question feedback on MCQ results** — learner cannot see which questions they got wrong and what the correct answer was.  
- **No time-remaining indicator** during timed assessments.  
- **No question navigation** during an assessment (no "next question", no "review before submit").  
- No quiz preview/practice mode (no ungraded attempt).  
**Severity:** 🟠 HIGH (no correct answer feedback) · 🟡 MEDIUM (others)

---

### Step 9: Submit Assignments

**Expected:** Learner uploads a file or writes a long-form text response for a written assessment.  
**Actual:** The assessment form accepts text answers for written questions. There is **no file upload option for learner submissions** — only text boxes.  
**Missing:**  
- **Assignment file upload** (PDF, DOCX) — critical for professional/vocational training  
- **Assignment submission draft** — save before submitting  
- **Submission confirmation email** to learner  
- **Resubmission pathway** if trainer returns work  
**Severity:** 🔴 CRITICAL for programmes requiring portfolio or written evidence submissions.

---

### Step 10: Receive Feedback

**Expected:** After marking, learner receives overall feedback and question-level comments from the trainer.  
**Actual:**  
- Trainers can write `overall_feedback` and `marker_feedback` per question.  
- Learner is notified (system notification) when results are released.  
- The result page (`assessment_result.html`) shows score, pass/fail.  
**Issue:** It is unclear from the template whether per-question feedback is shown to the learner. The marker's comments may not surface in the learner view.  
**Missing:**  
- **Rich feedback delivery** — only plain-text feedback, no rubric/criteria visibility  
- **Email notification** of result release (notifications are in-app only)  
**Severity:** 🟠 HIGH

---

### Step 11: Complete Course

**Expected:** When all required learning is done, the course status automatically updates to "completed".  
**Actual:** Course completion requires the **trainer or admin to manually change the enrolment status to "completed"** in the cohort view. There is no automatic completion trigger, even when all module assessments are passed.  
**Missing:**  
- **Auto-completion** when all published module assessments are passed  
- **Completion email** to learner  
- **Completion ceremony** / celebration UX (completion banner, badge, etc.)  
**Severity:** 🔴 CRITICAL — If a trainer forgets to mark completion, the learner never gets a certificate and their record stays "enrolled" indefinitely.

---

### Step 12: Obtain Certificate

**Expected:** Upon course completion, certificate is automatically issued and available to download.  
**Actual:** Certificate issuance is a **separate manual action** by trainer/admin (click "Issue Certificate" in the cohort view). It is not triggered by enrolment completion. If trainer forgets, learner never receives their certificate.  
**Missing:**  
- **Auto-certificate issuance** on enrolment completion  
- **Certificate available notification** with download link in email  
- **Certificate renewal reminders** as expiry approaches  
**Severity:** 🔴 CRITICAL (automation gap) · 🟠 HIGH (email notification)

---

### Step 13: View Learning History

**Expected:** Learner can see their complete history: all courses, results, certificates, and external training.  
**Actual:**  
- `/learner/training-record` — shows completed enrolments, certificates, and external training records. Good.  
- `/learner/results` — shows released submission results.  
- `/learner/certificates` — shows issued certificates with download.  
**Issues:**  
- Training record only shows **completed** enrolments (status == "completed"). In-progress and enrolled courses are not shown in the training record.  
- No CPD (Continuing Professional Development) hours total is shown.  
- No printable/exportable training transcript.  
- External training records have no evidence upload (no file attachment).  
**Severity:** 🟡 MEDIUM

---

### Phase 2 Summary — Learner Severity Count

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 5 |
| 🟠 HIGH | 5 |
| 🟡 MEDIUM | 4 |
| 🔵 LOW | 2 |

---

## PHASE 3 — TRAINER JOURNEY REVIEW

### Trainer Workflow

```
LOGIN → DASHBOARD → CREATE COURSE → ADD MODULES → ADD MATERIALS → CREATE ASSESSMENTS
    → ADD QUESTIONS → CREATE COHORT → ENROL LEARNERS → MONITOR PROGRESS
    → MARK SUBMISSIONS → ISSUE FEEDBACK → SET COMPLETION → ISSUE CERTIFICATE
    → GENERATE REPORTS
```

---

### Step 1: Create Course

**Expected:** Trainer creates a course with all relevant metadata.  
**Actual:** `/courses/create` — form includes: course code, title, awarding body, level, description, pass mark, assessment type, delivery mode, duration hours, cert validity years, credit value. This is a comprehensive set of fields. ✓  
**Issues:**  
- **No course image/thumbnail upload** — courses are text-only in the catalogue  
- **No version control** — no ability to create a new version of an existing course while keeping the old one for learners who are mid-way through  
- **No course template** — must start from scratch each time  
- **No prerequisite assignment UI** — prerequisites field exists in the model but the course form has no way to set it  
**Severity:** 🟡 MEDIUM (all are usability/completeness gaps, not blocking)

---

### Step 2: Create Modules

**Expected:** Trainer adds modules with titles, descriptions, and sequence.  
**Actual:** `/courses/{id}/modules/create` — title, description, delivery mode. Module ordering with up/down buttons exists. ✓  
**Issues:**  
- **No module duplication** — cannot copy a module from another course  
- **No bulk module creation**  
- **No module template** or lesson plan association  
**Severity:** 🔵 LOW

---

### Step 3: Create Lessons (Materials)

**Expected:** Trainer adds lessons/materials to each module.  
**Actual:** Materials support: PDF, DOCX, PPTX, MP4, PNG, JPG files, or URL links. MIME type validation prevents upload of incorrect file types. ✓  
**Issues:**  
- **No material reorder** — materials within a module have no order_index, no reorder controls  
- **No material duplication** across modules  
- **No rich text/SCORM/HTML content creation** — content must be a file, not created in-platform  
- **Video files are download-only** — no streaming player in the LMS  
- **No material version tracking** — if a PDF is replaced, old learners may have a different version  
**Severity:** 🟠 HIGH (no material ordering) · 🟡 MEDIUM (others)

---

### Step 4: Upload Materials

**Expected:** Files are uploaded and available immediately to enrolled learners.  
**Actual:** File upload with MIME check, size limit, UUID filename. Stored on local filesystem. ✓  
**Issues:**  
- **No progress indicator** on upload — large files show no feedback  
- **File size limit (50MB default)** may be too restrictive for video content  
- **No cloud storage** — files are local to the server. Not suitable for multi-server deployment  
- **No virus scanning** of uploaded files  
**Severity:** 🟡 MEDIUM

---

### Step 5: Create Quizzes / Assessments

**Expected:** Trainer creates quiz with questions, options, correct answers, time limits, and pass marks.  
**Actual:** Full assessment creation — type (MCQ/written/mixed), max attempts, pass mark, time limit, randomise questions/options, immediate results toggle. MCQ questions support 4 options (A–D) with correct answer flagged. ✓  
**Issues:**  
- **Maximum 4 MCQ options (A–D)** — cannot create 5-option questions  
- **No question bank import** — must create questions one by one; no bulk import (CSV)  
- **No question tagging/syllabus area filtering** on assessment view  
- **No partial marks** on MCQ (binary correct/incorrect)  
- **Assessment editing after learners have submitted** is possible — no warning that results may be affected  
- **No assessment preview** — trainer cannot see the assessment as a learner would  
**Severity:** 🟡 MEDIUM (all usability)

---

### Step 6: Create Written Assessments

**Expected:** Trainer creates written assignments that learners answer in text or upload files.  
**Actual:** Written question type exists. Text-box answers accepted.  
**Missing:**  
- **Learner file upload for submissions** — cannot receive portfolio evidence or document submissions  
- **Marking rubric** — no structured criteria/rubric for consistent marking  
- **Anonymous marking** — trainer can see learner name on submission  
- **Second marking / moderation** workflow  
**Severity:** 🔴 CRITICAL (file submission) · 🟡 MEDIUM (others)

---

### Step 7: Manage Learners

**Expected:** Trainer can view, add, remove, and communicate with learners in their cohorts.  
**Actual:** `/trainer/learners` shows all learners across trainer's cohorts. Enrolment status can be updated. Single-learner enrolment by email works. Bulk CSV import available. ✓  
**Issues:**  
- **No remove/withdraw button** for individual learner on trainer view — must change status to "dropped"  
- **No direct message to learner** from trainer — no trainer-to-learner messaging  
- **No learner profile view** for trainer — cannot see learner's contact details or organisation  
- **No cohort waiting list** management  
**Severity:** 🟠 HIGH (messaging) · 🟡 MEDIUM (others)

---

### Step 8: Monitor Progress

**Expected:** Trainer can see real-time progress of each learner in their cohort.  
**Actual:**  
- `/cohorts/{id}` — shows enrolment status, completion count, in-progress count, average score  
- Progress is assessment-pass based (not material view based)  
- No per-learner module breakdown on cohort view  
**Issues:**  
- **No per-learner progress drill-down** on the trainer cohort view — trainer sees aggregate stats but must run a report to see individual progress  
- **No last-activity date** per learner  
- **No at-risk learner flag** — no alert when a learner hasn't logged in or engaged for X days  
**Severity:** 🟠 HIGH

---

### Step 9: Mark Assignments

**Expected:** Trainer sees a marking queue, opens each submission, assigns marks, writes feedback, and releases result.  
**Actual:** `/assessments/marking` shows pending submissions. Marking form has per-question marks and feedback + overall feedback. Score is calculated automatically. ✓  
**Issues:**  
- **Trainer can see learner name** — not anonymised  
- **No draft/save** before submitting marks — if trainer navigates away, marks are lost  
- **No marking deadline** — no system reminder to trainers that submissions are waiting  
- **No moderation flag** — cannot flag a submission for second opinion  
**Severity:** 🟡 MEDIUM

---

### Step 10: Provide Feedback

**Expected:** Trainer writes feedback visible to learner, showing strengths, weaknesses, and guidance.  
**Actual:** Overall feedback and per-question marker comments are stored. Learner is notified.  
**Issues:**  
- **No feedback template** — freetext only  
- **No feedback visibility confirmation** — unclear if learner can see per-question feedback in their result view  
- **No resubmission instruction** — if learner fails, trainer cannot formally return work for resubmission  
**Severity:** 🟠 HIGH

---

### Step 11: Issue Certificates

**Expected:** Certificates are issued automatically or with one-click when a learner completes.  
**Actual:** Requires **two manual steps**: (1) trainer marks enrolment as "completed", (2) trainer clicks "Issue Certificate". Both steps must happen separately.  
**Missing:** Certificate auto-issuance on completion.  
**Severity:** 🔴 CRITICAL

---

### Step 12: Generate Reports

**Expected:** Trainer can generate and export comprehensive reports on their cohorts.  
**Actual:** Reports available: cohort summary, learner progress, certificate register, compliance CSV.  
**Issues:**  
- **No attendance report** — attendance is recorded but no report exists  
- **No assessment performance analysis** — no report showing question-level statistics (% correct per question)  
- **No report scheduling** (v2 subscription feature exists but not visible from trainer dashboard)  
- **No PDF export** — only CSV available for download  
**Severity:** 🟠 HIGH (attendance) · 🟡 MEDIUM (others)

---

### Phase 3 Summary — Trainer Severity Count

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH | 6 |
| 🟡 MEDIUM | 8 |
| 🔵 LOW | 1 |

---

## PHASE 4 — ADMINISTRATOR JOURNEY REVIEW

### Admin Workflow

```
LOGIN → DASHBOARD → USER MANAGEMENT → COHORT SETUP → ENROLMENT MANAGEMENT
    → MONITORING → REPORTS → SETTINGS → CERTIFICATES → AUDIT LOG → GDPR
```

---

### Step 1: Create Users

**Expected:** Admin can create individual users with roles and immediately activate them.  
**Actual:** `/admin/users/create` — full name, email, role, password. Role whitelist enforced. Password strength validated. Audit logged. ✓  
**Issues:**  
- **No bulk user import from admin panel** — only CSV enrolment into cohorts exists, not bulk user creation  
- **No user profile completeness indicator** — no alert when essential profile fields are missing  
- **No user invitation by email** — admin must set a password for the user (though force_password_change can be set)  
**Severity:** 🟡 MEDIUM

---

### Step 2: Assign Roles

**Expected:** Admin can change a user's role at any time.  
**Actual:** Role editing available in user edit form. VALID_ROLES whitelist enforced. ✓  
**Issue:** When a trainer is changed to a learner, their cohorts remain assigned to them. No reassignment prompt.  
**Severity:** 🟡 MEDIUM

---

### Step 3: Create Departments

**Expected:** Admin can create organisational departments and assign users/trainers to departments.  
**Actual:** **Departments do not exist** in this LMS. There is no Department model, no department assignment, and no department-level reporting.  
**Impact:** Organisations with multiple departments (e.g., HR, Operations, IT) cannot organise learners by department, cannot run department-specific compliance reports, and cannot assign mandatory training by department.  
**Severity:** 🟠 HIGH

---

### Step 4: Create Training Plans

**Expected:** Admin can create structured training plans assigning mandatory courses to roles or departments.  
**Actual:** **Training plans do not exist**. The closest feature is Learning Paths, which are sequences of optional courses. There is no mechanism to say "All staff in Role X must complete Course Y by Date Z".  
**Missing:**  
- Mandatory training flag per course  
- Training plan creation (role → required courses → deadline)  
- Automated enrolment for mandatory training  
**Severity:** 🔴 CRITICAL for compliance-focused organisations

---

### Step 5: Assign Mandatory Training

**Expected:** Admin can mark training as mandatory for specific users, roles, or departments.  
**Actual:** **Mandatory training assignment does not exist.** All enrolments are voluntary or admin-initiated case by case.  
**Impact:** Cannot enforce compliance training (health & safety, data protection, fire safety, etc.) systematically. This is the primary use case for many corporate and public sector LMS buyers.  
**Severity:** 🔴 CRITICAL

---

### Step 6: Monitor Compliance

**Expected:** Admin can see who has and hasn't completed mandatory training, with deadline tracking.  
**Actual:** Compliance report exists showing certificate status (active/expired), but it is based on certificate expiry dates — not mandatory training assignments (since those don't exist).  
**Issue:** No concept of "non-compliance" or overdue training — the system cannot flag a learner as non-compliant without mandatory training assignments.  
**Severity:** 🔴 CRITICAL

---

### Step 7: Run Reports

**Expected:** Admin can generate organisation-wide reports with filters, date ranges, and exports.  
**Actual:** Four reports: cohort summary, learner progress (individual), certificate register, compliance report (CSV).  
**Issues:**  
- **No date-range filtering** on any report  
- **No organisation-wide enrolment report** — only per-cohort  
- **No user activity report** — no record of logins, last access  
- **No course completion rate report** across all courses  
- **No trainer workload report**  
- **No assessment pass rate report** by question  
- **PDF export missing** — compliance report is CSV only  
**Severity:** 🟠 HIGH

---

### Step 8: Configure Notifications

**Expected:** Admin can configure what notifications are sent, when, to whom, and by what channel.  
**Actual:** System notifications exist (in-app). Email notifications are triggered at specific events (registration, approval, enrolment, results, certificates). No admin-configurable notification rules.  
**Issues:**  
- **Notification preferences** field exists on users (`notification_preferences = "all"`) but **no UI** to change it and no logic that respects different values  
- **No email templates** — emails are hardcoded plain HTML  
- **No SMS notifications**  
- **No notification digest** (daily summary)  
**Severity:** 🟠 HIGH

---

### Step 9: Manage Certificates

**Expected:** Admin can view all certificates, revoke, re-issue, and configure templates.  
**Actual:** Certificate list, revoke (with reason), download, and public verify all work. ✓  
**Issues:**  
- **No certificate template customisation** — hardcoded PDF layout with org name only  
- **No batch certificate issuance** — must issue one at a time per enrolment  
- **No expiry notification** system — expiring_certs count shown on dashboard but no automated email  
- **Certificate re-issue after renewal training** not automated  
**Severity:** 🟠 HIGH (batch issuance, expiry notifications) · 🟡 MEDIUM (template)

---

### Step 10: Manage Permissions

**Expected:** Admin can configure fine-grained permissions for each role.  
**Actual:** Permissions are **hardcoded by role** in the application. No admin-configurable permission matrix.  
**Impact:** Cannot grant a trainer access to reports without making them superadmin. Cannot restrict a superadmin from deleting courses.  
**Severity:** 🟡 MEDIUM (acceptable for most SME use cases)

---

### Step 11: Archive Courses

**Expected:** Admin can archive old courses — making them inactive but keeping historical records.  
**Actual:** **No archive feature exists**. Admin can only set `is_published = False` (unpublishes from learner catalogue) or **permanently delete** (loses all data).  
**Missing:**  
- Archive/unarchive toggle  
- Archived courses viewable by admin only  
- Historical enrolments preserved on archive  
**Severity:** 🟠 HIGH — risk of permanent data loss when "cleaning up" old courses

---

### Step 12: Audit Activity Logs

**Expected:** Admin can review who did what and when, with filtering and export.  
**Actual:** `/admin/audit-log` shows last 100 actions. Audit events: user create, approve, delete.  
**Issues:**  
- **Extremely limited audit events** — course creation, module changes, enrolments, assessments, markings, logins, and certificate issuance are NOT logged  
- **No date filtering**  
- **No user or action filtering**  
- **Limit of 100 records** — no pagination  
- **No export**  
**Severity:** 🔴 CRITICAL — ISO 9001, GDPR, and most compliance frameworks require complete audit trails of all training-related actions.

---

### Phase 4 Summary — Admin Severity Count

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 5 |
| 🟠 HIGH | 6 |
| 🟡 MEDIUM | 4 |
| 🔵 LOW | 0 |

---

## PHASE 5 — END-TO-END TESTING

### Scenario 1: Learner Enrols and Completes a Course

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Learner registers | Account created, pending | PASS | No confirmation email to learner |
| 2 | Admin approves | Account activated, email sent | PASS | ✓ |
| 3 | Admin enrols learner in cohort | Learner enrolled, notified | PASS | ✓ |
| 4 | Learner logs in, views dashboard | Sees enrolled cohort | PASS | Course title not prominent |
| 5 | Learner accesses course materials | Downloads files | PASS | No in-browser viewer |
| 6 | Learner takes MCQ assessment | Submits, sees score immediately | PASS | No correct answer feedback |
| 7 | Trainer marks enrolment complete | Status → completed | PASS (manual step) | Must be done manually |
| 8 | Trainer issues certificate | Certificate PDF generated | PASS (manual step) | Must be done manually |
| 9 | Learner downloads certificate | Downloads PDF | PASS | ✓ |

**Overall: PARTIAL PASS** — Core flow works but requires two manual admin/trainer interventions at completion.  
**Risk Rating:** 🟠 HIGH — Manual steps will be missed in busy organisations.

---

### Scenario 2: Trainer Creates a Course and Assesses a Learner

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Trainer creates course | Course saved, visible | PASS | ✓ |
| 2 | Trainer creates module | Module added | PASS | ✓ |
| 3 | Trainer uploads PDF material | File stored, accessible | PASS | MIME validation works |
| 4 | Trainer creates MCQ assessment | 4-option questions saved | PASS | Max 4 options only |
| 5 | Trainer creates cohort | Cohort linked to course | PASS | ✓ |
| 6 | Trainer enrols learner | Learner enrolled | PASS | ✓ |
| 7 | Learner takes assessment | Submits answers | PASS | No answer review before submit |
| 8 | MCQ auto-graded | Score calculated | PASS | No wrong-answer feedback |
| 9 | Trainer creates written question | Question saved | PASS | ✓ |
| 10 | Learner submits written answer | Submission stored | PASS | Text only, no file upload |
| 11 | Trainer marks written submission | Score + feedback recorded | PASS | No draft/save |
| 12 | Learner notified of result | In-app notification | PASS | No email notification |

**Overall: PASS with caveats**  
**Risk Rating:** 🟡 MEDIUM

---

### Scenario 3: Administrator Assigns Mandatory Training and Monitors Completion

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Admin identifies mandatory course | Marks as mandatory | FAIL | No mandatory training feature |
| 2 | Admin assigns to user group | All users in role enrolled | FAIL | No user group / mandatory enrolment |
| 3 | Admin sets deadline | Deadline recorded | FAIL | No deadline field on enrolments |
| 4 | System sends enrolment notification | Learners notified | FAIL | No automated mandatory enrolment |
| 5 | Admin monitors completion | Dashboard shows compliance | FAIL | Compliance report exists but no mandatory training to check |

**Overall: FAIL — This scenario is not supported by the current system.**  
**Risk Rating:** 🔴 CRITICAL

---

### Scenario 4: Learner Fails Assessment and Retries

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Learner takes MCQ, scores below pass mark | Score shown, FAIL indicated | PASS | ✓ |
| 2 | Learner is told how many attempts remain | Remaining attempts shown | FAIL | No "X attempts remaining" message displayed |
| 3 | Learner clicks Retry | Assessment re-taken | PASS | If max_attempts not reached |
| 4 | Learner has used all attempts | Retry blocked, error shown | PASS | "Maximum attempts reached" shown |
| 5 | Learner contacts trainer for reset | Trainer resets attempts | FAIL | No attempt reset feature for trainer |

**Overall: PARTIAL PASS**  
**Risk Rating:** 🟡 MEDIUM — Trainers cannot reset attempts; must delete submission from database.

---

### Scenario 5: Trainer Updates Course After Learners Enrolled

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Trainer edits course title | Title updated everywhere | PASS | ✓ |
| 2 | Trainer adds new module | Module added to course | PASS | ✓ |
| 3 | Trainer deletes a module with materials | Module and materials deleted | PASS | No warning that learners may be mid-module |
| 4 | Trainer edits MCQ questions | Questions updated | PASS | No warning that existing submissions used old questions |
| 5 | Trainer publishes new assessment | Assessment appears | PASS | No notification to enrolled learners of update |

**Overall: PASS — but with data integrity risks**  
**Risk Rating:** 🟠 HIGH — Editing questions after submission invalidates existing answers with no warning.

---

### Scenario 6: Administrator Removes a User

| Step | Action | Expected | Result | Issue |
|---|---|---|---|---|
| 1 | Admin navigates to user, clicks Delete | User deleted | PASS | ✓ |
| 2 | All user data (enrolments, submissions, certs) preserved | Cascade delete or orphan | FAIL | SQLAlchemy cascade delete may remove all related records — no data preservation mechanism |
| 3 | Audit log records deletion | Logged | PASS | ✓ |
| 4 | Alternative: deactivate instead of delete | User deactivated, data preserved | PASS | is_active=False works |

**Overall: PARTIAL PASS — deletion deletes user data. Recommended workflow is deactivation.**  
**Risk Rating:** 🔴 CRITICAL — Regulatory frameworks require training records to be kept for 3-7 years after employment ends. Deletion loses all records.

---

## PHASE 6 — LMS BEST PRACTICE REVIEW

### 6.1 Comparison Against Industry Standards

| Feature | Moodle | TalentLMS | LearnDash | Cornerstone | PLP LMS | Gap |
|---|---|---|---|---|---|---|
| Course catalogue with self-enrolment | ✓ | ✓ | ✓ | ✓ | ✗ | CRITICAL |
| In-browser content viewer (PDF/video) | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| SCORM / xAPI support | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Material completion tracking | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Sequential module locking | ✓ | ✓ | ✓ | ✓ | ✗ | MEDIUM |
| Mandatory training assignment | ✓ | ✓ | ✓ | ✓ | ✗ | CRITICAL |
| Departments / groups | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Automated certificate issuance | ✓ | ✓ | ✓ | ✓ | ✗ | CRITICAL |
| Learner assignment file upload | ✓ | ✓ | ✓ | ✓ | ✗ | CRITICAL |
| Correct answer feedback on MCQ | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Discussion forums | ✓ | ✓ | ✓ | ✓ | ✗ | MEDIUM |
| Gamification / badges | Plugins | ✓ | ✓ | ✓ | ✗ | LOW |
| Mobile app | ✓ | ✓ | ✓ | ✓ | ✗ | MEDIUM |
| Branded email notifications | ✓ | ✓ | ✓ | ✓ | ✗ | MEDIUM |
| Bulk certificate issuance | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Attempt reset by trainer | ✓ | ✓ | ✓ | ✓ | ✗ | MEDIUM |
| Course archiving | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Comprehensive audit trail | ✓ | ✓ | ✓ | ✓ | Partial | CRITICAL |
| Date-range report filtering | ✓ | ✓ | ✓ | ✓ | ✗ | HIGH |
| Training plans / compliance tracks | ✓ | ✓ | ✓ | ✓ | ✗ | CRITICAL |
| RPL / skill claims | Plugins | Partial | ✗ | ✓ | ✓ | ADVANTAGE |
| GDPR export | ✓ | ✓ | ✓ | ✓ | ✓ | ADVANTAGE |
| Data retention management | Partial | Partial | ✗ | ✓ | ✓ | ADVANTAGE |
| Cohort-based delivery | ✓ | ✓ | Partial | ✓ | ✓ | Meets standard |
| Multi-attempt assessments | ✓ | ✓ | ✓ | ✓ | ✓ | Meets standard |
| Public certificate verification | Partial | Partial | ✗ | Partial | ✓ | ADVANTAGE |

### 6.2 ISO 9001 Training Requirements Assessment

| ISO 9001 Clause | Requirement | Status |
|---|---|---|
| 7.2(a) | Determine necessary competence | ✗ No competency framework |
| 7.2(b) | Ensure personnel are competent | Partial — certificates issued but no competency mapping |
| 7.2(c) | Take actions where applicable | ✗ No mandatory training assignment |
| 7.2(d) | Retain documented information as evidence | ✓ Training records, certificates, audit log |
| 7.3 | Awareness of quality objectives | ✗ No awareness tracking within LMS |

### 6.3 Training Record Management Requirements

| Requirement | Status |
|---|---|
| Record of all training completed per individual | ✓ Enrolments + certs |
| Training completion dates | ✓ |
| Assessment scores retained | ✓ |
| Certificate expiry tracking | ✓ |
| Retention after employment ends (3-7 years) | ✓ GDPR anonymise preserves records |
| Evidence of learning materials viewed | ✗ Not tracked |
| Attendance records | Partial — recorded but not in reports |

---

## PHASE 7 — IMPROVEMENT REPORT

### 7.1 Critical Issues (Block Production Use for Compliance Organisations)

---

#### BPR-C01 — No Mandatory Training / Training Plans

**Description:** The system has no mechanism to assign mandatory training to users, roles, or groups. Learning paths exist but are optional.  
**Why It Matters:** The primary value proposition of an LMS for corporate and public sector is compliance enforcement. Without mandatory training, the system cannot serve health & safety, data protection, or induction training scenarios.  
**User Impact:** Admins cannot enforce compliance. Training remains voluntary. Non-completion cannot be tracked.  
**Suggested Fix:** Create a `MandatoryTraining` model linking a course to a role/user with a deadline. Auto-enrol affected users. Show compliance status on admin dashboard.

**OpenCode Prompt:**  
> Create a new model `plp_lms/models/mandatory_training.py` with fields: `id`, `course_id` (FK courses), `assigned_to_role` (nullable String), `assigned_to_user_id` (nullable FK users), `deadline_date` (Date, nullable), `created_by` (FK users), `created_at`. Create a router `routers/mandatory_training.py` with: GET `/admin/mandatory-training` (list all assignments), POST `/admin/mandatory-training/assign` (form with course_id, role or user_id, deadline), POST `/admin/mandatory-training/{id}/delete`. On assignment, auto-enrol all users matching the role into the next active cohort for that course. Add a compliance dashboard widget to `templates/admin/dashboard.html` showing: total mandatory trainings, % complete, overdue count. Add to `admin.py` router registration in `main.py`.

---

#### BPR-C02 — No Learner Self-Enrolment from Inside the Platform

**Description:** Learners cannot browse the course catalogue and self-enrol once logged in. Enrolment requires a trainer/admin action or a pre-shared token link.  
**Why It Matters:** Denies learner autonomy and creates administrative bottleneck for every enrolment.  
**User Impact:** Learners must contact an admin for every course. Prevents any self-directed learning.  
**Suggested Fix:** Add a "Browse & Enrol" page accessible to learners showing published courses with active cohorts. Include an "Enrol" button that either instantly enrols (if open) or sends an enrolment request to the trainer.

**OpenCode Prompt:**  
> In `plp_lms/routers/learner.py`, add a GET route `/learner/catalogue` that queries all published courses with at least one active cohort where the learner is not already enrolled. For each course, show title, description, delivery mode, duration. Add an "Enrol" button that POSTs to `/learner/catalogue/enrol` with `course_id`. The enrol handler should find the most appropriate active cohort (earliest start date, not at max_learners capacity) and create an `Enrolment` record with `enrolment_source="self"`. Send a notification to the course trainer and to the learner. If no cohort is available, show "No sessions currently available — contact your administrator." Create template `templates/learner/catalogue.html`. Add the catalogue link to the learner navigation bar.

---

#### BPR-C03 — No Automatic Course Completion and Certificate Issuance

**Description:** Course completion and certificate issuance are both separate manual steps requiring trainer/admin intervention after all assessments are passed.  
**Why It Matters:** Trainers will miss these steps. Learners complete training and receive no certificate or confirmation.  
**User Impact:** Learner frustration. Certificates not issued. Compliance gaps. Learner training record inaccurate.  
**Suggested Fix:** After an assessment is submitted and passes, check if all module assessments are now passed. If yes, auto-mark enrolment as "completed" and auto-issue a certificate.

**OpenCode Prompt:**  
> In `plp_lms/routers/assessments.py`, in the `submit_assessment` function, after `db.commit()` and score calculation, add an auto-completion check: (1) get the user's enrolment for this course, (2) call `get_learner_progress(db, user.id, assessment.course_id)`, (3) if `progress['progress_pct'] == 100`, set `enrolment.status = 'completed'` and `enrolment.completion_date = datetime.utcnow()`, (4) call `generate_certificate_pdf(db, user, course, enrolment)` and `send_certificate_notification(db, user.id, course.title, cert.certificate_number)`. Import `generate_certificate_pdf` from `services.certificate_service`. Do not issue a duplicate certificate if one already exists for that user and course. Add a flash message "Congratulations! You have completed this course. Your certificate is ready to download."

---

#### BPR-C04 — Learner Assignment File Upload Not Supported

**Description:** Written assessments accept text-only responses. Learners cannot submit PDF, DOCX, or image evidence for assignments.  
**Why It Matters:** Professional and vocational training frequently requires portfolio evidence, observation records, and witness testimonies in document form.  
**User Impact:** Cannot deliver NVQs, apprenticeships, or any competency-based qualification requiring document evidence.  
**Suggested Fix:** Add file upload to the assessment submission form for written-type assessments. Store file alongside the text answer. Show file in the marking form for trainer review.

**OpenCode Prompt:**  
> In `plp_lms/models/submission.py`, add `evidence_file_path = Column(String(500), nullable=True)` to the `Answer` model. In `plp_lms/routers/assessments.py`, in `submit_assessment`, change the handler to `async` and use `request.form()` to also capture file uploads from field name `evidence_{question_id}`. For written questions with an uploaded file, validate MIME type (PDF, DOCX, PNG, JPG only), save with UUID filename to UPLOAD_DIR, and store the path in `answer.evidence_file_path`. In `templates/shared/assessment_take.html`, for each written question add `<input type="file" name="evidence_{q.id}" accept=".pdf,.docx,.png,.jpg">` below the text area. In `templates/shared/marking_form.html`, show a download link for any uploaded evidence file next to the text answer.

---

#### BPR-C05 — Comprehensive Audit Trail Missing

**Description:** The audit log records only user create/approve/delete. All training events (enrolment, assessment submission, marking, certificate issuance, course changes) are unlogged.  
**Why It Matters:** ISO 9001, GDPR, Ofsted, and most regulatory frameworks require an unbroken audit trail of all training activities.  
**User Impact:** Organisation cannot demonstrate compliance during audits. Investigation of disputes impossible.  
**Suggested Fix:** Extend audit logging to all significant events throughout the system.

**OpenCode Prompt:**  
> In `plp_lms/models/audit.py`, confirm `AuditLog` has fields: `id, user_id, action, target_type, target_id, notes, timestamp`. In `plp_lms/routers/assessments.py`, after `submit_assessment` and `mark_submission`, add `db.add(AuditLog(user_id=user.id, action='submit_assessment'/'mark_submission', target_type='submission', target_id=submission.id, notes=f'Score: {score}%'))`. In `routers/cohorts.py`, after `enrol_learner`, add `AuditLog(action='enrol', target_type='enrolment', target_id=en.id, notes=f'User {learner.email} enrolled in cohort {cohort.name}')`. In `routers/certificates.py` after `generate_certificate_pdf`, add `AuditLog(action='issue_certificate', target_type='certificate', target_id=cert.id)`. In `routers/courses.py` after `create_course`, `edit_course`, `delete_course`, add corresponding audit entries. Update `admin/audit_log.html` to show 500 records with pagination and add filter dropdowns for `action` type and date range.

---

#### BPR-C06 — User Deletion Destroys Training Records

**Description:** Deleting a user removes all their enrolments, submissions, and certificates due to cascade relationships. Training records must be retained for 3-7 years.  
**Why It Matters:** GDPR Article 17 right to erasure conflicts with employment law obligations to retain training records. The system must support anonymisation (not deletion) as the default.  
**User Impact:** Organisation exposed to regulatory risk. Ex-employee training history lost.  
**Suggested Fix:** Replace the delete action with deactivation + GDPR anonymisation. Prevent hard deletion of users with any training history.

**OpenCode Prompt:**  
> In `plp_lms/routers/admin.py`, in the `delete_user` function, before deleting, check if the user has any `Enrolment`, `Submission`, or `Certificate` records. If yes, block the deletion with flash message: "This user has training records that must be retained. Use 'Deactivate' to disable their account, or use GDPR Anonymise to anonymise their personal data." Remove the delete button from `templates/admin/users.html` and replace with a "Deactivate" button (`POST /admin/users/{id}/deactivate` that sets `is_active=False`) and an "Anonymise (GDPR)" button. Only allow full deletion of users with zero training activity.

---

### 7.2 High Priority Issues

---

#### BPR-H01 — No Material Completion Tracking

**Description:** Downloading or viewing a material leaves no record in the system. Progress is assessment-only.  
**Why It Matters:** Regulators and awarding bodies may require evidence that learners accessed specific content.  
**Suggested Fix:** Log a `MaterialAccess` event (user_id, material_id, accessed_at) when a material is downloaded.

**OpenCode Prompt:**  
> Create `plp_lms/models/material_access.py` with `MaterialAccess(id, user_id, material_id, accessed_at)`. In `plp_lms/routers/courses.py` `download_material` handler, after confirming path safety, add `db.add(MaterialAccess(user_id=user.id, material_id=material_id, accessed_at=datetime.utcnow()))` and `db.commit()`. Update `progress_service.py` `get_learner_progress` to also report `materials_accessed` per module by querying `MaterialAccess`.

---

#### BPR-H02 — No Correct Answer Feedback on MCQ Results

**Description:** When a learner completes an MCQ and sees their result, they are not shown which questions they answered incorrectly or what the correct answer was.  
**Why It Matters:** Formative feedback is the foundation of learning. Without knowing what was wrong and why, learners cannot improve.  
**Suggested Fix:** On the result page, for each MCQ question show the learner's selected answer, the correct answer, and the question mark awarded.

**OpenCode Prompt:**  
> In `plp_lms/templates/shared/assessment_result.html`, in the questions loop, add: (1) show the learner's selected option text (join Answer to AnswerOption via selected_option_id), (2) show the correct answer option text (query AnswerOption where is_correct=True for that question), (3) highlight in green if correct, red if incorrect. In `plp_lms/routers/assessments.py` `view_result`, also pass `correct_answers = {q.id: db.query(AnswerOption).filter(AnswerOption.question_id == q.id, AnswerOption.is_correct == True).first() for q in questions}` to the template. Only show correct answers if `assessment.release_results_immediately == True` or if the submission status is `released`.

---

#### BPR-H03 — No Departments / Organisational Structure

**Description:** There is no way to organise users by department, team, or business unit.  
**Why It Matters:** Essential for organisation-wide compliance reporting, targeted mandatory training, and department-level dashboards.  
**Suggested Fix:** Add Department model, assign users to departments, filter reports by department.

**OpenCode Prompt:**  
> Create `plp_lms/models/department.py` with `Department(id, name, description, created_at)` and a `department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)` column on the `User` model. Create `plp_lms/routers/departments.py` with: GET `/admin/departments` (list), POST `/admin/departments/create`, POST `/admin/departments/{id}/delete`. Add `department_id` to the user edit form. Update the compliance report to add a department filter. Create Alembic migration.

---

#### BPR-H04 — No Assessment Attempt Reset by Trainer

**Description:** When a learner exhausts their maximum attempts, there is no UI for a trainer to grant an additional attempt.  
**Why It Matters:** Learners may have technical issues, misunderstand the assessment, or legitimately need a second chance under exceptional circumstances.  
**Suggested Fix:** Add a "Reset Attempts" button on the cohort learner view or marking queue.

**OpenCode Prompt:**  
> In `plp_lms/routers/assessments.py`, add `POST /assessments/{assessment_id}/reset-attempts/{user_id}` requiring `require_role("superadmin","trainer")`. The handler should delete all `Submission` records for that user+assessment and redirect back. In `templates/shared/cohort_view.html`, for each enrolled learner add a "Reset Attempts" dropdown per assessment. Log the reset action to `AuditLog`.

---

#### BPR-H05 — No In-Browser Content Viewer

**Description:** All materials (PDF, video) are download-only. Learners must use their own application to view content.  
**Why It Matters:** Download-only content breaks the learning experience, cannot be tracked, and creates a barrier on low-powered devices. Industry standard is an embedded viewer.  
**Suggested Fix:** Embed PDF.js for PDFs and an HTML5 video player for MP4s within the course view.

**OpenCode Prompt:**  
> In `plp_lms/templates/learner/course_view.html`, for each material where `material.file_type == 'pdf'`, add a PDF.js viewer using the CDN: `<iframe src="https://mozilla.github.io/pdf.js/web/viewer.html?file=/courses/materials/{material.id}/stream" width="100%" height="600"></iframe>`. Add a GET route `/courses/materials/{material_id}/stream` that returns `FileResponse` with media_type `application/pdf` (not octet-stream) and no Content-Disposition attachment header, so the browser renders it inline. For `file_type == 'mp4'`, add `<video controls width="100%"><source src="/courses/materials/{material_id}/stream" type="video/mp4"></video>`. Log access on the stream route as MaterialAccess.

---

#### BPR-H06 — No Course Archiving

**Description:** Courses can only be deleted (permanent) or unpublished (hidden). No archive state exists.  
**Why It Matters:** Old courses must be preserved for historical records and reporting while being removed from the active catalogue.  
**Suggested Fix:** Add `is_archived` boolean to Course. Archived courses are hidden from catalogue but accessible to admins and in historical reports.

**OpenCode Prompt:**  
> Add `is_archived = Column(Boolean, default=False)` to the `Course` model in `plp_lms/models/course.py`. In `routers/courses.py`, add `POST /courses/{course_id}/archive` and `POST /courses/{course_id}/unarchive` routes requiring superadmin. In `courses.list_courses`, add `Course.is_archived == False` to the filter for non-admin users. Add an "Archive" button to `templates/shared/course_view.html` (admin only). Create Alembic migration. Update the course list template to show an "Archived" badge.

---

#### BPR-H07 — Trainer Cannot Send Messages to Learners

**Description:** There is no direct messaging from trainer to individual learner or cohort group.  
**Why It Matters:** Trainers need to send feedback, reminders, and updates to learners without leaving the LMS.  
**Suggested Fix:** Extend the existing messages model to support trainer-to-learner messages.

**OpenCode Prompt:**  
> In `plp_lms/routers/v2_1.py`, add `POST /messages/send` accepting `recipient_id` (user_id), `subject`, `body`, `csrf_token` requiring `require_role("superadmin","trainer")`. Create the `Message` record and create a `Notification` for the recipient. In `templates/trainer/dashboard.html`, add a "Message Learner" button next to each learner in the cohort list. In `templates/v2/messages.html`, show a compose form at the top for trainers. Trigger an email notification to the recipient using `send_email`.

---

#### BPR-H08 — No Report Date Filtering

**Description:** All reports return all-time data with no date range filter.  
**Why It Matters:** Organisations need quarterly, annual, and period-specific reports.  
**Suggested Fix:** Add `date_from` and `date_to` parameters to all report endpoints.

**OpenCode Prompt:**  
> In `plp_lms/routers/reports.py`, add optional `date_from: Optional[str] = None` and `date_to: Optional[str] = None` query parameters to each report route. Pass these to the report service functions. In `plp_lms/services/report_service.py`, update each generate function to filter by `enrolled_at >= date_from` and `enrolled_at <= date_to` where provided. Add date picker inputs to `templates/shared/reports.html`.

---

### 7.3 Medium Priority Issues

---

#### BPR-M01 — Learner Dashboard Doesn't Show Course Name Prominently

**Description:** Dashboard cards show cohort name ("Autumn 2025 Cohort") not course name ("Health and Safety Level 2").  
**Suggested Fix:** Show both course title (large) and cohort name (small).

**OpenCode Prompt:**  
> In `plp_lms/templates/learner/dashboard.html`, in the enrolment card loop, change to show `enrolment.cohort.course.title` as the primary heading and `enrolment.cohort.name` as a subtitle in smaller text. Add a progress bar using `enrolment.cohort.course` progress data.

---

#### BPR-M02 — No Remaining Attempts Counter on Assessment

**Description:** Learners cannot see how many attempts they have left before being locked out.

**OpenCode Prompt:**  
> In `plp_lms/routers/assessments.py` `take_assessment`, pass `attempts_used = attempt_count` and `max_attempts = assessment.max_attempts` to the template. In `templates/shared/assessment_take.html`, add "Attempt {attempts_used + 1} of {max_attempts}" near the top of the form.

---

#### BPR-M03 — No Exportable Training Transcript for Learners

**Description:** Learners cannot download a PDF or printable summary of their complete training history.

**OpenCode Prompt:**  
> In `plp_lms/routers/learner.py`, add `GET /learner/training-record/export` that generates a PDF using ReportLab listing: learner name, all completed enrolments (course title, completion date, score), all certificates (cert number, issue date, expiry), and external training records. Return as a `FileResponse`. Add "Download Training Record" button to `templates/learner/training_record.html`.

---

#### BPR-M04 — No Batch Certificate Issuance

**Description:** Certificates must be issued one at a time per enrolment. When a cohort of 30 completes, trainer must click 30 times.

**OpenCode Prompt:**  
> In `plp_lms/routers/certificates.py`, add `POST /certificates/issue-batch` accepting a list of `enrolment_ids`. Iterate and call `generate_certificate_pdf` for each completed enrolment without an existing certificate. Add a "Issue All Certificates" button to `templates/shared/cohort_view.html` that submits all completed enrolment IDs in a form.

---

#### BPR-M05 — No Certificate Expiry Email Notifications

**Description:** Expiring certificates appear on admin dashboard count but no email is sent to the learner or admin.

**OpenCode Prompt:**  
> In `plp_lms/services/scheduler_service.py`, add a new scheduled job `notify_expiring_certs` running daily at 08:00. Query certificates where `expiry_date` is within 30, 14, and 7 days and `revoked == False`. For each, send an email to the learner saying their certificate expires in X days and they should re-enrol. Also send a summary email to all superadmins. Add the scheduler job in `main.py` lifespan.

---

#### BPR-M06 — No Prerequisite Enforcement

**Description:** The `prerequisites` JSON field exists on Course but is never checked — learners can take advanced courses without completing prerequisite courses first.

**OpenCode Prompt:**  
> In `plp_lms/routers/assessments.py` in `take_assessment`, after the enrolment check, query `course.prerequisites`. If prerequisites is a non-empty list of course_ids, check that the learner has a completed enrolment for each. If any prerequisite is not met, return the template with `error="You must complete {prerequisite_course.title} before taking this assessment."` In `learner.course_view`, show a "Prerequisites Required" banner if not met.

---

#### BPR-M07 — Notification Preferences Field Has No Logic

**Description:** `user.notification_preferences = "all"` is stored but never read. All notifications fire regardless of user preference.

**OpenCode Prompt:**  
> In `plp_lms/services/notification_service.py` and `email_service.py`, before sending a notification or email, check `user.notification_preferences`. Define three values: `'all'` (default), `'in_app_only'` (suppress emails), `'none'` (suppress all). Respect these values in every `send_email` call and `create_notification` call. Add a notification preferences dropdown to `templates/learner/profile.html` with options: All notifications, In-app only, None. Wire to `POST /learner/profile` handler.

---

#### BPR-M08 — Attendance Not Included in Reports

**Description:** Attendance is recorded on cohort sessions but there is no attendance report and attendance is not factored into completion.

**OpenCode Prompt:**  
> In `plp_lms/services/report_service.py`, add `generate_attendance_report(db, cohort_id)` that queries `AttendanceRecord` for the cohort and returns per-learner attendance percentage. Add a new route `GET /reports/attendance?cohort_id=X` in `routers/reports.py`. Add an "Attendance Report" tab to `templates/shared/reports.html`. Also add attendance % to the cohort view page for each enrolled learner.

---

### 7.4 Low Priority Issues

---

#### BPR-L01 — No Course Thumbnail / Image

**Description:** Course catalogue shows text only. No image or branding per course.

**OpenCode Prompt:**  
> Add `thumbnail_path = Column(String(500), nullable=True)` to the `Course` model. In `courses.create_course` and `edit_course` handlers, add optional image upload (PNG/JPG, max 2MB). In `templates/shared/courses.html` and `learner/catalogue.html`, show thumbnail using `<img src="/courses/{course.id}/thumbnail">`. Add a GET `/courses/{course_id}/thumbnail` route returning the image file.

---

#### BPR-L02 — No Discussion Forums

**Description:** No learner-to-learner or learner-to-trainer discussion space exists within the LMS.

**OpenCode Prompt:**  
> Create `models/discussion.py` with `DiscussionThread(id, course_id, user_id, title, body, created_at)` and `DiscussionReply(id, thread_id, user_id, body, created_at)`. Add routes in a new `routers/discussion.py`. Link threads to courses. Show threads on the learner course view and trainer course view. Send a notification to the thread author when a reply is added.

---

#### BPR-L03 — No Search Functionality

**Description:** No search bar exists for courses, learners, or cohorts.

**OpenCode Prompt:**  
> Add a search bar to the navigation layout in `templates/layout.html`. Add a GET `/search?q={query}` route that queries: `Course.title`, `User.full_name`, `User.email`, `Cohort.name`, and returns a combined results page grouped by type. Require authentication.

---

#### BPR-L04 — Account Lockout Duration Not Shown

**Description:** When locked out, learner sees "Account locked. Try again later." with no indication of when they can retry.

**OpenCode Prompt:**  
> In `plp_lms/routers/auth.py` login handler, after `check_account_locked(user)` returns True, calculate remaining minutes: `remaining = max(0, int((user.locked_until - datetime.utcnow()).total_seconds() / 60))`. Change the error message to `f"Account locked. Please try again in {remaining} minutes."`.

---

### Final Priority Summary

| Category | Count | Themes |
|---|---|---|
| 🔴 CRITICAL | 6 | Mandatory training, self-enrolment, auto-completion, file submission, audit trail, data deletion |
| 🟠 HIGH | 8 | Material tracking, MCQ feedback, departments, attempt reset, content viewer, archiving, messaging, reports |
| 🟡 MEDIUM | 8 | Dashboard UX, transcript, batch certs, expiry alerts, prerequisites, notifications, attendance, thumbnails |
| 🔵 LOW | 4 | Search, forums, account lockout message, course images |

---

*End of Report — PLP LMS Business Process Validation Review — 13 June 2026*
