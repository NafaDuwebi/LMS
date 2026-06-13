# PLP LMS — User Guide
**PL Projects Ltd | B Corp Certified Project Management Consultancy**  
**Version 1.0 | June 2026**

---

## Contents

1. [Getting Started](#1-getting-started)
2. [Default Accounts](#2-default-accounts)
3. [User Roles Overview](#3-user-roles-overview)
4. [Starting and Stopping the System](#4-starting-and-stopping-the-system)
5. [Superadmin Guide](#5-superadmin-guide)
6. [Trainer Guide](#6-trainer-guide)
7. [Learner Guide](#7-learner-guide)
8. [Observer Guide](#8-observer-guide)
9. [Navigation Tips](#9-navigation-tips)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Getting Started

### Accessing the system locally
1. Double-click the **"PLP LMS"** desktop shortcut, or run `start_lms.bat`
2. Your browser will open automatically at `http://127.0.0.1:8000`
3. Log in using one of the accounts listed in Section 2

### Accessing the demo (shared link)
If someone has shared a live demo link with you (e.g. `https://batting-happy-deepen.ngrok-free.dev`):
1. Open the link in your browser
2. You may see a brief security page — click **"Visit Site"** to continue
3. Log in using the credentials provided

> **First login:** You will be asked to change your password the first time you log in.

---

## 2. Default Accounts

| Role | Email | Password |
|---|---|---|
| Superadmin | admin@plprojects.co.uk | Admin1234! |
| Trainer | trainer@plprojects.co.uk | Trainer1234! |
| Observer | observer@plprojects.co.uk | Observer1234! |
| Learner 1 | learner1@example.com | Learner1234! |
| Learner 2 | learner2@example.com | Learner1234! |

> ⚠️ Change all default passwords before using the system with real learners.

---

## 3. User Roles Overview

The system has four roles. Each role sees a different navigation menu and has different permissions.

| Role | What they can do |
|---|---|
| **Superadmin** | Full control — users, courses, cohorts, settings, reports, GDPR, audit log |
| **Trainer** | Manage their assigned cohorts, mark assessments, take attendance, view learners |
| **Learner** | Access courses, take assessments, view results and certificates, submit skill claims |
| **Observer** | Read-only access to cohorts and reports — no editing |

---

## 4. Starting and Stopping the System

### Starting (quickest way)
Double-click the **PLP LMS** desktop shortcut.  
This starts the server and opens the system in your browser automatically.

### Starting (manually)
Open a terminal, navigate to the `plp_lms` folder and run:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000` in your browser.

### Sharing with someone externally (ngrok)
If you want to share the system with an external user (e.g. for a demo):

1. Make sure the system is running locally (step above)
2. Open a second terminal and run:
```bash
ngrok http --domain=batting-happy-deepen.ngrok-free.dev 8000
```
3. Share the URL `https://batting-happy-deepen.ngrok-free.dev` with your colleague
4. Keep both terminal windows open while they are using it

### Stopping the system
Press `Ctrl+C` in the terminal window, or close the terminal window.

---

## 5. Superadmin Guide

Log in as `admin@plprojects.co.uk` to access all features below.

---

### 5.1 Managing Users

1. Click **Users** in the top navigation bar
2. Click **Create User** to add a new learner, trainer, or observer
3. Fill in their name, email, role, and organisation
4. The user receives a welcome email with login instructions
5. To edit a user, click **Edit** next to their name
6. To deactivate a user, click **Edit** and toggle the Active switch off

---

### 5.2 Managing Courses

#### Creating a new course
1. Go to **Courses** → **Create Course**
2. Fill in:
   - Title, course code, awarding body, level
   - Duration (hours), pass mark (default 55% for APM courses)
   - Assessment type (MCQ / Written / Mixed)
   - Delivery mode (Online / Classroom / Blended)
   - Certificate validity (leave 0 for no expiry)
3. Click **Save**

#### Adding modules to a course
1. Open the course and click **Add Module**
2. Give the module a title and description
3. Set the delivery mode for that module
4. Use the up/down arrows to reorder modules
5. Toggle **Published** when the module is ready for learners

#### Adding materials to a module
1. Open a module and click **Add Material**
2. Upload a file (PDF, PPTX, DOCX, MP4 — up to 500MB) or paste a video link
3. Give the material a title
4. Materials appear to learners in the order you add them

#### Adding learning outcomes
1. Open a course and go to the **Learning Outcomes** tab
2. Click **Add Outcome** and enter the outcome text
3. Tag it to the relevant syllabus area (e.g. APM, IRM)

#### Publishing a course
Toggle the **Published** switch on the course page when it is ready for learners to see.

---

### 5.3 Managing Cohorts

#### Creating a cohort
1. Go to **Cohorts** → **Create Cohort**
2. Select a course, trainer, start and end dates, venue, and max learners
3. Click **Save** — an enrolment token and link are generated automatically

#### Enrolling learners
**Individually:**
1. Open a cohort and click **Enrol Learner**
2. Search for the learner by email and click **Enrol**

**In bulk (CSV upload):**
1. Open a cohort and click **Bulk Upload**
2. Download the CSV template
3. Fill in columns: `full_name`, `email`, `organisation`
4. Upload the completed CSV
5. The system creates accounts and sends welcome emails automatically

#### Sharing the enrolment link
1. Open a cohort and click **Copy Enrolment Link**
2. Send the link to learners — they can self-register using it

---

### 5.4 Assessments

#### Creating an assessment
1. Open a course and go to **Assessments** → **Create Assessment**
2. Choose type: MCQ, Written, Mixed, or Practical Sign-off
3. Set pass mark, max attempts, and time limit (optional)
4. Toggle **Randomise questions** and **Randomise options** as needed
5. Toggle **Release results immediately** if learners should see results straight away

#### Adding questions
1. Open an assessment and click **Add Question**
2. For MCQ: enter the question, add 4 options, and mark the correct one
3. For written: enter the question and maximum marks
4. Tag each question to a syllabus area for reporting purposes

#### Using the question bank
1. Go to **Assessments** → **Question Bank**
2. Create reusable questions tagged by course and syllabus area
3. When building an assessment, click **Import from Bank** to pull questions in

---

### 5.5 Learning Paths

Learning paths group courses into a structured curriculum with enforced sequencing.

#### Creating a learning path
1. Go to **Paths** → **Create Path**
2. Give the path a title and description
3. Click **Add Course** and select courses in the order learners should complete them
4. Toggle **Unlock on previous completion** for each course to enforce sequencing
5. Publish the path when ready

Learners who enrol in a path are automatically enrolled in the first course. When they complete it, they are automatically enrolled in the next.

---

### 5.6 Document Requirements

Use this to require learners to upload documents (e.g. ID, proof of qualification) before accessing course content.

1. Open a cohort and go to the **Documents** tab
2. Click **Add Requirement** and enter the document label and instructions
3. Learners see an upload prompt when they access the course
4. Go to **Document Review** in the sidebar to approve or reject submissions
5. Learners cannot access course materials until all required documents are approved

---

### 5.7 Skills Management

Skills allow learners on apprenticeship or practical courses to claim mastery of specific competencies, which a reviewer then approves.

#### Setting up skills
1. Open a course and go to the **Skills** tab
2. Click **Add Skill** and enter the skill title, description, and evidence required
3. Assign a reviewer (trainer, external assessor, or admin)

#### Reviewing skill claims
1. Go to **Skills Review** in the sidebar
2. You will see all pending claims with the learner's comment and evidence
3. Click **Approve** or **Reject** — add a comment explaining your decision
4. The learner is notified automatically

---

### 5.8 RPL (Recognition of Prior Learning)

Learners can claim credit for courses they believe they already qualify for based on previous experience or qualifications.

1. Learners submit an RPL claim from their Training Record page
2. Go to **RPL Review** in the sidebar to see pending claims
3. Review the evidence and click **Approve** or **Reject**
4. Approved claims automatically mark the course as complete on the learner's record

---

### 5.9 Reports

#### Built-in reports
Go to **Reports** to access:
- **Cohort Summary** — enrolments, completions, pass rate, average score
- **Learner Progress** — module-by-module breakdown per learner
- **Assessment Analysis** — per-question performance and difficulty indicators
- **Certificate Register** — all issued certificates with dates
- **Compliance Report** — certificates expiring or already expired
- **Attendance Summary** — per cohort and per session

All reports can be exported to **CSV** or **PDF** using the buttons at the top of each report.

#### Report subscriptions
Automatically email a report to any recipient on a schedule:
1. Go to **Subscriptions** → **New Subscription**
2. Select the report, enter recipient email addresses (comma separated)
3. Set frequency: daily / weekly / monthly
4. Set the send time
5. Click **Save** — the report will be emailed automatically on schedule

---

### 5.10 GDPR Data Retention

1. Go to **Retention** in the top navigation bar
2. Records flagged for review (past their retention date) are listed here
3. For each flagged record choose:
   - **Anonymise** — removes personal data (name, email, phone) but keeps learning records for audit
   - **Extend** — sets a new review date with a justification note
   - **Delete** — permanently removes all data (irreversible — use with caution)
4. All actions are recorded in the audit log

---

### 5.11 System Settings

Go to **Settings** to configure:

| Setting | Description |
|---|---|
| Organisation name | Displayed in the header and on certificates |
| Logo | Upload your organisation logo |
| Default pass mark | Applied to new courses unless overridden |
| Attendance threshold | Minimum % attendance required for certificate (default 80%) |
| Data retention period | Years to keep learner records (default 3) |
| Max upload size | Maximum file size for material uploads (default 500MB) |
| Session timeout | How long before an inactive user is logged out |

---

### 5.12 Audit Log

Go to **Audit Log** to view a full history of all system activity including:
- Logins and logouts
- Enrolments and withdrawals
- Assessment submissions and marking
- Certificate issues and revocations
- File uploads and deletions
- GDPR actions

Use the filters to search by user, action type, or date range.

---

## 6. Trainer Guide

Log in as `trainer@plprojects.co.uk` to access the trainer features below.

---

### 6.1 Your Dashboard

Your dashboard shows:
- Your assigned cohorts and their progress
- Pending assessment submissions to mark
- Upcoming sessions

---

### 6.2 Taking Attendance

1. Open a cohort from your dashboard
2. Click the **Attendance** tab
3. Click **Add Session** and enter the session date
4. For each learner mark: **Present**, **Absent**, **Excused**, or **Exempt**
5. Add a note against any learner if needed
6. Click **Save**

Attendance percentage is calculated automatically and shown on the learner's record. Learners below the threshold are flagged.

---

### 6.3 Marking Assessments

1. Click **Pending Submissions** in your navigation bar
2. Click **Mark** next to any submission
3. For written questions: enter the marks awarded and add feedback comments
4. MCQ questions are already auto-marked — you can review but not change them
5. Click **Save and Release** to send results to the learner
6. If you want to hold results: click **Save Draft** and release later

> If you suspect malpractice, tick the **Flag for malpractice** box before saving. The submission goes into a separate review queue for the admin.

---

### 6.4 Practical Sign-off

For courses with practical or on-the-job elements:
1. Open a cohort and click on a learner's name
2. Go to the **Assessments** tab
3. Find the practical assessment and click **Sign Off**
4. Add a comment confirming what was observed
5. Click **Confirm** — the learner's assessment is marked complete

---

### 6.5 Reviewing Skill Claims

1. Click **Skills Review** in your navigation bar
2. You will see pending claims from learners in your courses
3. Read the learner's comment and review any uploaded evidence
4. Click **Approve** or **Reject** and add a comment
5. The learner is notified immediately

---

### 6.6 Generating Reports

From any cohort you can generate:
- **Attendance Register** (PDF) — printable register for the session
- **Progress Report** (CSV/PDF) — all learners' module and assessment progress
- **Completion Certificate** — issue manually if needed

---

## 7. Learner Guide

Log in as `learner1@example.com` to explore the learner experience.

---

### 7.1 Your Dashboard

Your dashboard shows:
- Active courses with a progress bar
- Upcoming session dates
- Recent notifications (results, certificates, messages)
- Any documents or actions still required from you

---

### 7.2 Accessing Your Courses

1. Click **My Courses** in the top navigation bar
2. Click **Continue** on any course to open it
3. Work through each module in order — click on a module to open it
4. Read or download the materials provided
5. When you are ready, click **Start Assessment** to attempt the quiz or assignment

---

### 7.3 Uploading Required Documents

Some courses require you to upload documents before you can access materials:
1. You will see a banner saying **"Action required: upload your documents"**
2. Click the banner or go to the **Documents** tab in your course
3. Upload each required file (e.g. passport photo, valid ID)
4. Wait for admin approval — you will be notified when approved

---

### 7.4 Taking Assessments

1. From inside a course, click on the assessment name
2. Click **Start Attempt**
3. Answer all questions — for timed exams a countdown timer is shown
4. Click **Submit** when finished
5. For MCQ assessments your result is shown immediately
6. For written assessments your trainer will mark and release results

> You may have a limited number of attempts — check the assessment details before starting.

---

### 7.5 Skill Claims

For apprenticeship or practical courses you may need to claim skills:
1. Go to **My Skills** on your course page
2. Find a skill you have demonstrated
3. Click **Submit Claim**
4. Write a brief description of what you did and how it demonstrates the skill
5. Upload any supporting evidence (optional)
6. Click **Submit** — your reviewer will be notified
7. Check back for the outcome: Approved or Rejected (with feedback)

---

### 7.6 RPL (Recognition of Prior Learning)

If you believe you already have the knowledge or qualification for a course:
1. Go to your **Training Record**
2. Click **Submit RPL Claim**
3. Select the course you are claiming credit for
4. Enter details of your prior learning: course name, provider, completion date
5. Upload evidence (e.g. certificate, transcript)
6. Write a short statement explaining how it is relevant
7. Submit — an admin will review and notify you of the outcome

---

### 7.7 Learning Paths

1. Click **Paths** in the top navigation bar
2. Browse available learning paths
3. Click **Enrol** on a path to join it
4. You will be automatically enrolled in the first course
5. Complete each course to unlock the next one in the path
6. Your overall path progress is shown as a step-by-step indicator

---

### 7.8 Downloading Certificates

1. Click **Certificates** in the top navigation bar
2. All your earned certificates are listed here
3. Click **Download** to save a PDF copy
4. Each certificate has a unique verification number
5. Share the verification link with employers: `https://[your-domain]/verify/[certificate-number]`

---

### 7.9 Your Training Record

1. Click your name in the top right → **Training Record**
2. You will see all your completed courses, scores, and certificates
3. To add external training (e.g. a course from another provider):
   - Click **Add External Training**
   - Enter the course name, provider, completion date, and hours
   - Upload a certificate or evidence if available
4. Click **Download Transcript** to get a PDF of your full training history

---

### 7.10 Messages

1. Click the **envelope icon** in the top navigation bar
2. All system emails are stored here (enrolment confirmations, results, reminders)
3. Click any message to read it in full
4. Useful if a system email went to your spam folder

---

## 8. Observer Guide

Log in as `observer@plprojects.co.uk` for read-only access.

As an observer you can:
- View all active cohorts and their progress dashboards
- Access all built-in reports (cohort summary, learner progress, certificates)
- Export reports to CSV or PDF

You cannot enrol learners, edit any content, or mark assessments.

---

## 9. Navigation Tips

- The **top navigation bar** changes based on your role — you will only see what is relevant to you
- The **bell icon** (🔔) shows unread notifications — click it to see results, reminders, and messages
- The **envelope icon** (✉️) opens your Message Centre
- **Green badges** — active or successful items
- **Amber badges** — items requiring your attention
- **Red badges** — errors, rejected items, or urgent actions
- Click your **name** in the top right to access your profile, change your password, or log out

---

## 10. Troubleshooting

| Problem | Solution |
|---|---|
| Server won't start | Make sure port 8000 is free. In terminal run: `taskkill /F /IM python.exe` then try again |
| Login page not loading | Check the terminal — is uvicorn running? If not, start it again |
| Login fails | Check caps lock is off. Use **Forgot Password** or ask an admin to reset |
| Shared link not working | Check both terminal windows (uvicorn and ngrok) are still open and running |
| ngrok link shows "Visit Site" warning | Normal — click "Visit Site" to continue |
| Page shows an error | Refresh the page. If it persists, copy the error and contact Nafa |
| File upload fails | Check the file is under 500MB and is a supported format (PDF, PPTX, DOCX, MP4) |
| Certificate won't generate | The learner must have a passing score and (if applicable) met the attendance threshold |
| Can't see a feature | Your role may not have access — ask the superadmin to check your role |
| Assessment won't submit | Check all questions are answered. If timed, check the timer hasn't expired |
| Bulk CSV upload fails | Check the CSV has columns: `full_name`, `email`, `organisation` with no blank rows |

---

## Quick Reference — Demo Accounts

| Role | Email | Password | Best for showing |
|---|---|---|---|
| Superadmin | admin@plprojects.co.uk | Admin1234! | Full system, settings, reports, GDPR |
| Trainer | trainer@plprojects.co.uk | Trainer1234! | Attendance, marking, cohort management |
| Learner | learner1@example.com | Learner1234! | Course access, assessments, certificates |
| Observer | observer@plprojects.co.uk | Observer1234! | Reports and dashboards (read-only) |

---

## Demo URL (ngrok)

While the demo is running, the system is accessible at:

👉 **https://batting-happy-deepen.ngrok-free.dev**

> This link only works while Nafa's PC is on and both terminal windows (uvicorn + ngrok) are running.  
> For a permanent hosted version, contact Nafa at PL Projects Ltd.

---

*PLP LMS User Guide — PL Projects Ltd*  
*B Corp Certified Project Management Consultancy*  
*© 2026 PL Projects Ltd. All rights reserved.*
