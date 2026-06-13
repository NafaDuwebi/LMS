# PLP Learning Management System — User Guide

**Version:** 1.0 | **Prepared by:** CESUS Development Team | **Date:** June 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites & Starting the System](#2-prerequisites--starting-the-system)
3. [User Roles](#3-user-roles)
4. [Part A — Superadmin Workflows](#part-a--superadmin-workflows)
5. [Part B — Trainer Workflows](#part-b--trainer-workflows)
6. [Part C — Learner Workflows](#part-c--learner-workflows)
7. [Part D — Observer Workflows](#part-d--observer-workflows)
8. [Part E — Advanced Features](#part-e--advanced-features)
9. [Troubleshooting](#9-troubleshooting)
10. [Password Policy](#10-password-policy)

---

## 1. System Overview

PLP LMS is a web-based Learning Management System built with FastAPI and PostgreSQL. It supports five user roles: **Superadmin**, **Trainer**, **Learner**, **Observer**, and **External Assessor**. The system manages the full training lifecycle: course creation, cohort management, learner enrolment, assessment delivery, marking, certificate issuance, and compliance reporting.

All interaction happens through a web browser. No software installation is required on the learner's machine.

---

## 2. Prerequisites & Starting the System

### What you need before starting

- Python 3.10 or later installed
- PostgreSQL running locally (or a remote connection configured in `.env`)
- The project folder: `PLP Learning management system/`
- All Python dependencies installed

### Step-by-step: Start the system

**Step 1.** Open a PowerShell or Command Prompt window. Navigate to the project folder:

```powershell
cd "C:\Users\drnaf\OneDrive\Desktop\CESUS\Mateen Project\PLP Learning management system"
```

**Step 2.** Activate the virtual environment (if one exists):

```powershell
# Windows
.venv\Scripts\activate

# If no virtual environment, skip this step
```

**Step 3.** Install dependencies (first time only):

```powershell
pip install -r plp_lms/requirements.txt
```

**Step 4.** Start the application from inside the `plp_lms` folder:

```powershell
cd plp_lms
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Step 5.** Open a web browser and go to:

```
http://localhost:8000
```

You should see the PLP LMS login page. The system is now running.

> **Note:** Keep the PowerShell window open. Closing it stops the server. To stop the server at any time, press `Ctrl + C` in the PowerShell window.

---

## 3. User Roles

| Role | What they can do |
|------|-----------------|
| **Superadmin** | Full system access: manage users, courses, cohorts, assessments, certificates, reports, settings, audit log |
| **Trainer** | Manage their assigned cohorts, record attendance, mark assessments, review skill/RPL claims |
| **Learner** | Access enrolled courses, take assessments, view results, download certificates, manage their profile |
| **Observer** | Read-only access to courses, cohorts, and assessments — cannot modify anything |
| **External Assessor** | Review submitted skill and RPL claims for sign-off |

---

## Part A — Superadmin Workflows

### A1. First Login & Account Setup

The first superadmin account is created directly in the database during initial setup. Once the system is running, log in using those credentials.

**Step 1.** Go to `http://localhost:8000/auth/login`

**Step 2.** Enter your email address or username and password, then click **Login**.

**Step 3.** If prompted to accept GDPR/data processing consent, read the notice and click **I Consent** to proceed.

**Step 4.** If the system forces a password change (first login), enter your current password, choose a new strong password, and click **Change Password**.

You will land on the **Dashboard**, which shows an overview of active cohorts, pending approvals, and recent activity.

---

### A2. Creating User Accounts

You can create accounts directly as a superadmin, or approve self-registered users (see A3).

**Step 1.** From the navigation menu, go to **Admin → Users**.

**Step 2.** Click **Create User**.

**Step 3.** Fill in the form:
- **Full Name** — learner's or staff member's full name
- **Email Address** — must be unique in the system
- **Role** — select from `learner`, `trainer`, `observer`, `superadmin`, `external_assessor`
- **Password** — must meet the password policy (see section 10)

**Step 4.** Click **Create User**.

The user is created immediately and is active. They will be prompted to change their password on first login.

> **Tip:** If you want the user to set their own password via an email link, use the Cohort Enrolment method (A11), which sends a welcome email with a secure setup link.

---

### A3. Approving Registered Users

When a learner self-registers at `/auth/register`, their account is created in an **inactive** state and requires admin approval before they can log in.

**Step 1.** You will receive a notification (bell icon, top navigation) showing a new registration is pending.

**Step 2.** Go to **Admin → Users**.

**Step 3.** Find the user in the list. Inactive users show a pending status.

**Step 4.** Click **Approve** next to their name.

The account is activated and the learner receives an email notification that they can now log in.

To **deny** (delete) a registration, click **Delete** instead. This cannot be undone.

---

### A4. Managing System Settings

**Step 1.** Go to **Admin → Settings**.

**Step 2.** You can update:
- **Organisation Name** — displayed throughout the system
- **Minimum Attendance Threshold (%)** — percentage required for completion (default: 80%)
- **Data Retention Period (years)** — how long learner data is kept for GDPR purposes (default: 3 years)
- **Maximum Upload Size (MB)** — largest file a trainer can upload per material (default: 500MB)

**Step 3.** Click **Save Settings**. Changes take effect immediately without restarting.

---

### A5. Creating a Course

Courses are the central content containers. A course must exist before you can create cohorts.

**Step 1.** Go to **Courses** in the top navigation.

**Step 2.** Click **Create Course**.

**Step 3.** Fill in the required fields:
- **Course Code** — a short reference code (e.g. `PLP-001`)
- **Title** — the full course name

**Step 4.** Fill in the optional fields as needed:
- **Awarding Body** — e.g. City & Guilds, Pearson
- **Level** — e.g. Level 2, Level 3
- **Description** — a summary shown to learners
- **Pass Mark (%)** — default is 55%. This applies to all assessments in the course unless overridden per assessment
- **Assessment Type** — `mcq`, `written`, or `mixed`
- **Delivery Mode** — `online`, `face-to-face`, or `blended`
- **Duration (hours)** — total expected learning hours
- **Certificate Validity (years)** — 0 means the certificate does not expire
- **Credit Value** — number of credits awarded on completion

**Step 5.** Click **Create Course**.

The course is created in **draft** (unpublished) status. Learners cannot see it until it is published (see A9).

---

### A6. Adding Modules to a Course

Modules are chapters or units within a course.

**Step 1.** Go to **Courses** and click on the course title to open it.

**Step 2.** Scroll to the **Modules** section and click **Add Module**.

**Step 3.** Fill in:
- **Title** — the module name
- **Description** — optional summary
- **Delivery Mode** — `online`, `face-to-face`, or `blended`

**Step 4.** Click **Create Module**.

The module appears in the course view. Repeat for each module.

**To reorder modules:** Use the **↑** and **↓** arrows next to each module to change its position in the sequence.

**To edit a module:** Click **Edit** next to the module title, update the fields, and save.

**To delete a module:** Click **Delete** next to the module. This also removes all materials attached to that module.

---

### A7. Uploading Course Materials

Materials are files (PDFs, videos, presentations, images) or links attached to a module.

**Step 1.** Open a course, then click **Add Material** next to a module.

**Step 2.** Fill in:
- **Title** — descriptive name for the material
- **File Type** — select from `pdf`, `docx`, `pptx`, `mp4`, `png`, `jpg`
- **Upload File** — click Choose File and select your file. Maximum size is set in Admin Settings (default 500MB). Allowed types: PDF, DOCX, PPTX, MP4, PNG, JPG.
- **OR URL** — paste an external link (e.g. a YouTube video or SharePoint document) instead of uploading a file

**Step 3.** Click **Upload Material**.

The material appears under the module. Learners enrolled in the course can download or view it.

---

### A8. Adding Learning Outcomes

Learning outcomes define what a learner will be able to do after completing the course. They are also used for skills sign-off and RPL claims.

**Step 1.** Open a course and scroll to the **Learning Outcomes** section.

**Step 2.** Click **Add Outcome**.

**Step 3.** Enter:
- **Outcome Text** — e.g. "Demonstrate safe manual handling techniques"
- **Syllabus Area** — optional tag linking this outcome to a syllabus section

**Step 4.** Click **Add Outcome**. Repeat for each outcome.

---

### A9. Publishing a Course

A course must be published before it can be assigned to cohorts and seen by learners.

**Step 1.** Open the course.

**Step 2.** Click **Edit Course**.

**Step 3.** Tick the **Published** checkbox.

**Step 4.** Click **Save**. The course is now live.

> **Important:** Only published courses appear in the cohort creation dropdown.

---

### A10. Creating a Cohort

A cohort is a delivery instance of a course — a group of learners completing the course together within a defined period.

**Step 1.** Go to **Cohorts** in the navigation.

**Step 2.** Click **Create Cohort**.

**Step 3.** Fill in:
- **Cohort Name** — e.g. "Manual Handling — September 2026"
- **Course** — select the published course this cohort delivers
- **Trainer** — assign a trainer (optional but recommended)
- **Start Date** and **End Date**
- **Maximum Learners** — the cohort cap (default: 30)
- **Delivery Mode** — `online`, `face-to-face`, or `blended`
- **Venue** — physical location (for face-to-face cohorts)

**Step 4.** Click **Create Cohort**.

The cohort is created and an **Enrolment Token** is automatically generated. This token can be used to create a self-registration link (see A11).

---

### A11. Enrolling Learners into a Cohort

There are three ways to enrol learners.

#### Method 1 — Enrol by email address (recommended for small groups)

**Step 1.** Open the cohort from **Cohorts**.

**Step 2.** In the **Enrol Learner** section, type the learner's email address and click **Enrol**.

- If the email matches an existing active user, they are enrolled immediately.
- If the email is new, an account is created for them and a **welcome email** with a password-setup link is sent automatically.

**Step 3.** The learner's name appears in the Enrolments table with status `enrolled`.

#### Method 2 — Self-registration via enrolment link

**Step 1.** Open the cohort and copy the **Enrolment Token** shown in the cohort details.

**Step 2.** Share this URL with prospective learners:

```
http://localhost:8000/auth/join/TOKEN
```

Replace `TOKEN` with the actual token. When a learner visits this URL, they are taken to the registration form pre-linked to the cohort. After registering, they appear in the user list as pending approval.

**Step 3.** Approve the registration (see A3). Once approved, their enrolment in the cohort is confirmed.

#### Method 3 — Bulk import via CSV

See A12 below.

---

### A12. Bulk Importing Learners via CSV

This method lets you enrol many learners at once by uploading a CSV file.

**Step 1.** Prepare a CSV file with the following columns (header row required):

```
full_name,email
Jane Smith,jane.smith@example.com
John Doe,john.doe@example.com
```

**Step 2.** Open the cohort.

**Step 3.** In the **Bulk Import** section, click **Choose File**, select your CSV, and click **Import Learners**.

The system creates accounts for any emails not already in the system and sends each new learner a welcome email with a password-setup link. Existing users are enrolled directly without a new email.

**Step 4.** The cohort enrolments table updates to show all imported learners.

---

### A13. Creating an Assessment

Assessments are attached to a course and optionally to a specific module.

**Step 1.** Go to **Assessments** in the navigation.

**Step 2.** Click **Create Assessment**.

**Step 3.** Fill in:
- **Course** — the course this assessment belongs to
- **Module** — optional: link to a specific module
- **Title** — assessment name
- **Type** — `mcq` (multiple choice), `written` (free-text, requires manual marking), or `mixed`
- **Maximum Attempts** — how many times a learner can attempt this assessment
- **Pass Mark (%)** — leave blank to inherit the course pass mark
- **Time Limit (minutes)** — optional: leave blank for no time limit
- **Randomise Questions** — tick to shuffle question order per attempt
- **Randomise Options** — tick to shuffle MCQ answer options per attempt
- **Release Results Immediately** — tick to show MCQ results as soon as submitted; untick to hold results until manually released

**Step 4.** Click **Create Assessment**.

---

### A14. Adding Questions to an Assessment

**Step 1.** Open an assessment from the Assessments list.

**Step 2.** Scroll to the **Questions** section and click **Add Question**.

**Step 3.** For an MCQ question, fill in:
- **Question Text** — the question
- **Question Type** — select `mcq`
- **Marks** — points awarded for a correct answer (default: 1)
- **Option A, B, C, D** — the answer choices
- **Correct Answer** — select which option letter is correct (A, B, C, or D)

**Step 4.** For a written question, fill in:
- **Question Text** — the question
- **Question Type** — select `written`
- **Marks** — maximum marks available. These must be awarded manually during marking.

**Step 5.** Click **Add Question**. Repeat for each question.

**To edit a question:** Click **Edit** next to it, update the fields, and save.

**To delete a question:** Click **Delete** next to it.

---

### A15. Publishing an Assessment

Learners cannot take an assessment until it is published.

**Step 1.** Open the assessment.

**Step 2.** Click **Edit Assessment**.

**Step 3.** Tick the **Published** checkbox.

**Step 4.** Click **Save**.

---

### A16. Issuing Certificates

Certificates can be issued to any learner whose enrolment status has been marked as **Completed**.

**Step 1.** Go to **Certificates** in the navigation.

**Step 2.** The page lists all enrolments eligible for a certificate (status = completed, no existing certificate).

**Step 3.** Click **Issue Certificate** next to a learner's name.

A certificate PDF is generated and saved. The learner receives a notification and can download it from their profile. The certificate is assigned a unique certificate number that can be publicly verified at:

```
http://localhost:8000/certificates/verify/CERTIFICATE_NUMBER
```

**To revoke a certificate:**

**Step 1.** Open the Certificates list.

**Step 2.** Click **Revoke** next to the certificate.

**Step 3.** Enter a reason for revocation and confirm.

---

### A17. Viewing the Audit Log

Every significant action in the system (user creation, approval, deletion, login) is recorded in the audit log.

**Step 1.** Go to **Admin → Audit Log**.

**Step 2.** The log shows the 100 most recent events: who performed the action, what the action was, the target, and the timestamp.

---

### A18. GDPR Data Export

You can export all data held about an individual user as a ZIP file containing a JSON file.

**Step 1.** Go to **Admin → Users**.

**Step 2.** Find the user and click **GDPR Export** next to their name.

The browser downloads a file called `gdpr_export_user_ID.zip` containing all enrolments, submissions, certificates, training records, RPL claims, and skill claims for that user.

---

### A19. Viewing Reports

**Step 1.** Go to **Reports** in the navigation.

**Step 2.** Available reports:

| Report | What it shows |
|--------|--------------|
| **Cohort Summary** | All learners in a cohort with status, enrolment date, completion date, and final score. Exportable as CSV. |
| **Learner Progress** | Detailed progress for a single learner in a specific course. |
| **Certificate Register** | All certificates issued, with certificate number, learner, course, and expiry. |
| **Compliance Report** | Certificates approaching expiry or already expired. Exportable as CSV. |

**Step 3.** To export a report as CSV, click the **Download CSV** button next to the report.

---

## Part B — Trainer Workflows

### B1. Logging In as a Trainer

**Step 1.** Go to `http://localhost:8000/auth/login`.

**Step 2.** Enter your email (or username) and password.

**Step 3.** Accept GDPR consent if prompted. Change your password if prompted.

You land on the Dashboard showing your assigned cohorts and any submissions waiting to be marked.

---

### B2. Viewing Your Cohorts

**Step 1.** Click **My Cohorts** in the navigation (or go to **Trainer → Cohorts**).

**Step 2.** The list shows all cohorts assigned to you. Click a cohort name to open it.

The cohort view shows:
- Total enrolled learners
- Number completed / in progress
- Average score
- Individual enrolment records with each learner's status

---

### B3. Recording Attendance

**Step 1.** Open a cohort and click **Attendance**.

**Step 2.** To create a new session, enter the session date in the **Add Session** field and click **Add Session**. A new column appears in the attendance register.

**Step 3.** For each learner in the session column, select **Present** or **Absent**. Add optional notes in the notes field.

**Step 4.** Click **Save Attendance**.

**To delete a session:** Click **Delete** next to the session date column header. All attendance records for that date are removed.

---

### B4. Marking Submitted Assessments

Written or mixed assessments require manual marking after a learner submits them.

**Step 1.** Go to **Assessments → Marking Queue** (or **Trainer → Submissions**).

**Step 2.** The queue lists all submissions waiting for marking, ordered by submission date.

**Step 3.** Click **Mark** next to a submission.

**Step 4.** The marking form shows each question, the learner's answer, and a **marks** field. Enter the marks awarded for each question (cannot exceed the maximum for that question).

**Step 5.** Add per-question **feedback** in the feedback fields (optional but recommended).

**Step 6.** Add **Overall Feedback** at the bottom.

**Step 7.** Click **Submit Marking**.

The system calculates the total score, determines pass/fail against the pass mark, marks the submission as **Released**, and sends the learner a notification with their result.

---

### B5. Updating Enrolment Status

After a learner completes all requirements for a cohort, update their status to trigger certificate eligibility.

**Step 1.** Open a cohort.

**Step 2.** Find the learner in the enrolments table.

**Step 3.** In the **Status** dropdown next to their name, select the appropriate status:
- `enrolled` — default, just enrolled
- `in_progress` — actively studying
- `completed` — finished all requirements
- `withdrawn` — voluntarily left
- `deferred` — postponed to a later cohort

**Step 4.** Click **Update Status**.

Setting status to `completed` also records the completion date and calculates the data retention review date.

---

### B6. Reviewing Skills & RPL Claims

When learners submit skill or RPL claims, they appear in the review queues.

**Step 1.** Go to **Skills → Review Queue** or **RPL → Review Queue**.

**Step 2.** Click **Review** next to a claim to open the full submission, including any uploaded evidence.

**Step 3.** Set the decision to **Approved** or **Rejected**, add feedback, and submit.

The learner is notified of the outcome automatically.

---

## Part C — Learner Workflows

### C1. Self-Registration

If you have received a cohort enrolment link, use it to register directly into that cohort. Otherwise, use the standard registration form.

**Step 1.** Go to `http://localhost:8000/auth/register`

(or open the enrolment link you received, e.g. `http://localhost:8000/auth/join/TOKEN`)

**Step 2.** Fill in:
- **Full Name**
- **Username** — a unique display name with no spaces
- **Email Address**
- **Password** — must meet the password policy (see section 10)
- **Organisation** — optional

**Step 3.** Tick **I consent to my data being processed** (required).

**Step 4.** Click **Register**.

Your account is created but **inactive**. You will see a message that your registration is pending admin approval. You cannot log in until a superadmin approves your account.

Once approved, you will receive an email notification and can then log in.

---

### C2. Logging In as a Learner

**Step 1.** Go to `http://localhost:8000/auth/login`.

**Step 2.** Enter your email address (or username) and password.

**Step 3.** If your account was created by an admin, you may be asked to set a password first via a link sent to your email. Check your inbox for a "Set your PLP LMS password" email.

**Step 4.** Accept GDPR consent if prompted.

You land on the Dashboard showing your enrolled courses.

**Forgotten your password?**

Click **Forgot Password** on the login page, enter your email address, and follow the link sent to your inbox. Reset links expire after 1 hour.

---

### C3. Browsing and Accessing Your Courses

**Step 1.** Go to **My Courses** (from the Dashboard or the navigation menu).

**Step 2.** Your enrolled courses are listed with progress indicators.

**Step 3.** Click a course title to open it.

Inside the course view you can:
- Read the course description and learning outcomes
- Browse modules in order
- Download or view materials attached to each module
- See available assessments

---

### C4. Taking an Assessment

**Step 1.** From inside a course, click the assessment title in the **Assessments** section, or go to **Assessments** from the main navigation and find the published assessment.

**Step 2.** Click **Take Assessment**.

The system checks that:
- The assessment is published
- You are enrolled in the course
- You have not exceeded the maximum number of attempts

**Step 3.** Answer each question:
- For **MCQ** questions: click the radio button next to your chosen answer.
- For **written** questions: type your answer in the text field.

**Step 4.** When finished, click **Submit Assessment**.

- For MCQ assessments with immediate results, you will be redirected to your result page straight away.
- For written or mixed assessments, your submission goes to the marking queue and you will be notified when it has been marked.

---

### C5. Viewing Your Results

**Step 1.** Go to **My Results** from the navigation.

**Step 2.** Released results are listed with the assessment title, your score, pass/fail status, and submission date.

**Step 3.** Click **View** next to any result to see your full submission: each question, your answer, whether it was correct, marks awarded, and any feedback from the marker.

---

### C6. Downloading Your Certificate

Certificates are issued by the admin or trainer once your enrolment is marked as completed.

**Step 1.** Go to **My Certificates** (or **Learner → Certificates**).

**Step 2.** Your certificates are listed with the course title, issue date, certificate number, and expiry (if applicable).

**Step 3.** Click **Download** to save the certificate PDF to your device.

**To share or verify your certificate:**

Give the recipient the certificate number and ask them to visit:

```
http://localhost:8000/certificates/verify/CERTIFICATE_NUMBER
```

---

### C7. Updating Your Profile

**Step 1.** Click your name in the top-right corner of the screen, then click **Profile** (or go to `/learner/profile`).

**Step 2.** Update any of the following:
- **Full Name**
- **Organisation**
- **Job Title**
- **Phone Number**

**Step 3.** Click **Save Profile**.

**To change your password:**

On the same profile page, scroll to the **Change Password** section. Enter your current password, your new password twice, and click **Change Password**.

---

### C8. Adding an External Training Record

You can log training you completed outside of PLP LMS to keep a complete CPD record.

**Step 1.** Go to **Training Record** from the navigation.

**Step 2.** Click **Add External Training**.

**Step 3.** Fill in:
- **Title** — name of the training/course
- **Provider** — who delivered it
- **Type** — e.g. `external_training`, `cpd`, `qualification`
- **Completion Date**
- **Hours** — duration in hours

**Step 4.** Click **Add Record**.

The record appears in your Training Record alongside your PLP LMS completions and certificates.

**To edit or delete an external record:** Click **Edit** or **Delete** next to the record.

---

### C9. Submitting a Skill Claim

Skills are practical competencies defined within a course. You can submit evidence to claim a skill for review.

**Step 1.** Go to **Skills → My Skills** from the navigation.

**Step 2.** Locate the skill you want to claim (your trainer or admin will let you know which skills are available for your course).

**Step 3.** Click **Claim Skill** next to the skill title.

**Step 4.** Fill in the evidence form — describe how you demonstrated the skill and upload any supporting files.

**Step 5.** Click **Submit Claim**.

Your claim is sent to the trainer/assessor review queue. You will receive a notification when it is approved or rejected.

---

### C10. Submitting an RPL Claim

Recognition of Prior Learning (RPL) allows you to claim credit for skills or qualifications you already hold.

**Step 1.** Go to **RPL** from the navigation (or find it under your course).

**Step 2.** Click **Submit RPL Claim**.

**Step 3.** Fill in:
- **Course** — the course you are claiming RPL against
- **Claim Statement** — describe your prior learning and how it maps to the course outcomes
- **Evidence** — upload supporting documents (certificates, transcripts, references)

**Step 4.** Click **Submit**.

Your claim enters the RPL review queue. You will be notified of the outcome.

---

## Part D — Observer Workflows

Observers have read-only access to published content. They cannot create, edit, or delete anything.

**Step 1.** Log in at `http://localhost:8000/auth/login` using your observer credentials.

**Step 2.** Available sections:

| Section | URL | What you can see |
|---------|-----|-----------------|
| **Courses** | `/observer/courses` | All published courses |
| **Course Detail** | `/observer/courses/{id}` | Modules, learning outcomes, assessments |
| **Cohorts** | `/observer/cohorts` | All active cohorts |
| **Cohort Detail** | `/observer/cohorts/{id}` | Enrolment list |
| **Assessments** | `/observer/assessments` | All published assessments |
| **Reports** | `/reports` | All standard reports (read only) |

Observers can also download CSV reports from the Reports section.

---

## Part E — Advanced Features

### E1. Learning Paths

Learning paths group multiple courses into a structured sequence, where learners must complete each course before unlocking the next.

**Creating a Learning Path (Superadmin/Trainer)**

**Step 1.** Go to **Learning Paths** from the navigation.

**Step 2.** Click **Create Learning Path**.

**Step 3.** Enter a **Title** and optional **Description**, then click **Create**.

**Step 4.** On the learning path detail page, use the **Add Course** section to add published courses. They are added in the order you add them.

**Step 5.** To remove a course from the path, click **Remove** next to it.

**Learner enrolment in a Learning Path**

When a learner visits a learning path and clicks **Enrol**, they are automatically enrolled in the first course's cohort (if an active cohort exists). Subsequent courses unlock automatically as each previous course is completed.

---

### E2. Document Requirements

You can require learners to submit specific documents (ID, qualifications, declarations) before their enrolment is processed.

**Step 1.** Go to a cohort.

**Step 2.** In the **Document Requirements** section, click **Add Requirement**.

**Step 3.** Specify the document type, description, and whether it is mandatory.

**Step 4.** Learners see the document requirements when they view their enrolment and can upload their files through the submission form.

**Step 5.** Trainers and admins review submissions and mark each document as **Accepted** or **Rejected**.

---

## 9. Troubleshooting

| Symptom | Likely cause | Solution |
|---------|-------------|----------|
| Login page shows "Account pending approval" | Self-registered account not yet approved | Superadmin must approve the account in Admin → Users |
| Login page shows "Account locked" | Too many failed login attempts | Wait 15 minutes and try again, or contact superadmin to reset |
| "Not enrolled in this course" when taking assessment | Learner not in an active enrolment for this course's cohort | Enrol the learner in a cohort that delivers this course |
| "Certificate already issued" error | Certificate was already generated for this enrolment | Check the Certificates list for the existing certificate |
| "File type not permitted" on upload | File extension or MIME type is not in the allowed list | Use PDF, DOCX, PPTX, MP4, PNG, or JPG only |
| "File exceeds maximum size" | File is larger than the configured max upload size | Compress the file, or increase Max Upload MB in Admin → Settings |
| Assessment not visible to learner | Assessment is not published | Edit the assessment and tick Published |
| Course not in cohort dropdown | Course is not published | Edit the course and tick Published |
| Application crashes on startup | Database connection failed | Check PostgreSQL is running and DATABASE_URL in plp_lms/.env is correct |

---

## 10. Password Policy

All passwords in PLP LMS must meet the following requirements:

- Minimum **8 characters**
- At least **one uppercase letter** (A–Z)
- At least **one lowercase letter** (a–z)
- At least **one digit** (0–9)
- At least **one special character** (e.g. `! @ # $ % ^ & * ( )`)

Passwords that do not meet these requirements will be rejected with an error message.

**After 5 consecutive failed login attempts**, an account is locked for a period of time. Contact the superadmin to unlock it sooner if needed.

---

*End of User Guide — PLP LMS v1.0*
