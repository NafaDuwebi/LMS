# PLP Learning Management System
## Complete User Guide

**Organisation:** PL Projects Ltd — B Corp Certified Project Management Consultancy
**System:** PLP Learning Management System (LMS)
**Version:** 2.1
**Last Updated:** June 2026
**Classification:** Internal — All Staff

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Getting Started — All Roles](#3-getting-started--all-roles)
4. [Administrator Guide](#4-administrator-guide)
5. [Trainer Guide](#5-trainer-guide)
6. [Learner Guide](#6-learner-guide)
7. [Observer & External Assessor Guide](#7-observer--external-assessor-guide)
8. [End-to-End Workflow](#8-end-to-end-workflow)
9. [Additional Features](#9-additional-features)
10. [Frequently Asked Questions](#10-frequently-asked-questions)
11. [Troubleshooting Guide](#11-troubleshooting-guide)
12. [Best Practices](#12-best-practices)
13. [Quick Start Guides](#13-quick-start-guides)

---

## 1. Introduction

### Purpose

The PLP Learning Management System (LMS) is the central platform for delivering, managing, and tracking all training and professional development activity at PL Projects Ltd. It provides a single environment where staff can access courses, complete assessments, earn certificates, and maintain a verifiable training record.

### Key Benefits

- **Centralised training** — all courses, materials, and records in one place
- **Role-based access** — each user sees only what is relevant to their role
- **Automated certification** — certificates are issued automatically upon successful completion
- **Compliance tracking** — GDPR consent, attendance, and completion records are maintained automatically
- **Flexible assessment** — supports multiple-choice, written, short-answer, and mixed assessments
- **Audit-ready** — full training history is logged and reportable at any time

### Intended Users

| Role | Who This Is |
|---|---|
| Administrator (Superadmin) | HR, operations, and system managers responsible for the platform |
| Trainer | Subject matter experts who create and deliver training content |
| Learner | All staff members completing training |
| Observer | Managers or stakeholders with read-only visibility of training activity |
| External Assessor | Third-party assessors who mark specific submitted assessments |

---

## 2. System Overview

### What the System Does

The PLP LMS manages the full training lifecycle from content creation through to certification. Administrators configure the platform and manage users. Trainers build courses and mark assessments. Learners complete training and earn certificates. Every action is logged, creating a complete and auditable training record for the organisation.

### Main Features

- User registration, role assignment, and account management
- Course and module creation with file-based learning materials
- Cohort management — grouping learners with assigned trainers and schedules
- Four assessment types: Multiple Choice (MCQ), Written, Short Answer, and Mixed
- Automated MCQ scoring; trainer-led marking for written and mixed assessments
- Certificate issuance, download, and revocation
- Learning paths that bundle multiple courses into a structured programme
- Skills tracking and evidence-based portfolio management
- Training records and reporting dashboard
- Notification system for key events
- Bulk learner import via CSV
- GDPR consent management

### User Roles and Permissions

| Feature | Admin | Trainer | Learner | Observer | Ext. Assessor |
|---|:---:|:---:|:---:|:---:|:---:|
| Manage all users | ✓ | | | | |
| Create / publish courses | ✓ | ✓ | | | |
| Manage cohorts | ✓ | | | | |
| Upload learning materials | ✓ | ✓ | | | |
| Create assessments | ✓ | ✓ | | | |
| Mark written assessments | ✓ | ✓ | | | ✓ |
| Take assessments | | | ✓ | | |
| View own training record | | | ✓ | | |
| View all training records | ✓ | | | ✓ | |
| Issue / revoke certificates | ✓ | | | | |
| Access reporting | ✓ | ✓ (own) | | ✓ | |
| System settings | ✓ | | | | |

---

## 3. Getting Started — All Roles

### 3.1 Logging In

1. Open your web browser and navigate to the LMS URL provided by your administrator.
2. On the login page, enter your **Email address or Username** in the first field.
3. Enter your **Password** in the second field.
4. Click **Sign In**.
5. If your credentials are correct you will be taken to your dashboard.

> **Note:** After five consecutive failed login attempts your account will be locked for 30 minutes. Contact your administrator if you need your account unlocked sooner.

> **Forgot your password?** Click the **Forgot password?** link on the login page and follow the instructions sent to your registered email address.

---

### 3.2 First Login — Account Setup Wizard

All accounts created by an administrator require you to complete a one-time setup before you can access the system.

1. Log in with the temporary credentials provided to you.
2. You will be automatically redirected to the **Complete Your Account** page.
3. The page has two sections:

**Set Your Password**
- Enter a new password in the **New Password** field.
- Your password must be at least 8 characters and include an uppercase letter, a lowercase letter, a number, and a symbol.
- This replaces your temporary password immediately.

**GDPR Consent**
- Read the consent statement carefully.
- Tick the checkbox to confirm you consent to the processing of your personal data for training administration purposes.

4. Click **Complete Setup**.
5. You will be taken directly to your dashboard. This setup step will not appear again.

---

### 3.3 Navigating the System

The top navigation bar is always visible. The options shown depend on your role.

| Role | Navigation Items |
|---|---|
| Administrator | Dashboard, Courses, Cohorts, Assessments, Paths, Reports, Messages, Users, Settings |
| Trainer | Dashboard, My Courses, Catalogue, Assessments, Paths, Skills, Training Record, Results, Certificates, Messages |
| Learner | Dashboard, My Courses, Catalogue, Paths, Skills, Training Record, Results, Certificates, Messages |
| Observer | Dashboard, Courses, Reports |

The **notification bell** (top right) shows alerts for items requiring your attention. Your **account name** (top right) links to your profile.

---

### 3.4 Your Profile

1. Click your name in the top-right corner of any page.
2. Select **Profile** from the dropdown.
3. You can update your **full name**, **email address**, and **department**.
4. To change your password, scroll to the **Change Password** section, enter your current password, then enter and confirm your new password.
5. Click **Save Changes**.

---

## 4. Administrator Guide

### 4.1 Administrator Responsibilities

As an administrator you are responsible for:

- Setting up and maintaining all user accounts
- Creating and publishing courses
- Building and managing cohorts
- Overseeing the full training lifecycle
- Generating compliance and activity reports
- Configuring system-wide settings

---

### 4.2 Logging In and Dashboard Overview

After logging in you are taken to the **Admin Dashboard**, which shows a summary of current system activity.

| Stat Card | What It Shows |
|---|---|
| Learners | Total active learner accounts |
| Trainers | Total active trainer accounts |
| Active Cohorts | Cohorts currently running |
| Courses | Total published courses |
| Pending Marking | Submissions awaiting trainer review |
| Expiring Certs | Certificates expiring within 30 days |
| Enrolment Requests | Self-registration requests awaiting approval |

**Quick Actions** on the dashboard provide one-click access to: New Course, New Cohort, Add User, and Marking Queue.

**Recent Enrolments** shows the latest learner enrolments across all cohorts.

---

### 4.3 User Management

#### Creating a New User

1. Click **Users** in the top navigation.
2. Click **Add User** (or use the Quick Action on the dashboard).
3. Complete the form:
   - **Full Name** — the user's display name
   - **Email** — used for login and notifications (must be unique)
   - **Role** — select Administrator, Trainer, or Learner
   - **Department** — optional, used for reporting
   - **Temporary Password** — a password the user will be required to change on first login
4. Click **Create User**.
5. The user will receive their login credentials and must complete the Account Setup Wizard on first login.

> **Username:** Usernames are generated automatically from the email address (the part before the @ symbol). You do not need to enter one.

> **First Login Flags:** All admin-created accounts automatically require a password change and GDPR consent on first login.

---

#### Editing a User

1. Go to **Users**.
2. Find the user in the list and click **Edit** next to their name.
3. Update the relevant fields (name, email, role, department, active status).
4. To force a password change on the user's next login, tick **Force Password Change**.
5. Click **Save Changes**.

---

#### Deactivating a User

1. Go to **Users** and find the user.
2. Click **Edit**.
3. Untick the **Active** checkbox.
4. Click **Save Changes**.

The user will no longer be able to log in. Their training records and history are preserved.

---

#### Approving Self-Registered Users

When a user registers through the public registration form, their account is inactive until approved.

1. Go to **Users**.
2. Accounts awaiting approval are shown with a **Pending** status.
3. Click **Edit** on the relevant account.
4. Set the role, assign a department if needed, and tick **Active**.
5. Click **Save Changes**. The user can now log in.

---

#### Bulk Importing Learners via CSV

1. Go to **Users**.
2. Click **Bulk Import**.
3. Download the CSV template provided.
4. Fill in the template with one user per row (full name, email, role, department).
5. Upload the completed CSV file.
6. Review the preview and click **Confirm Import**.
7. All imported users will be created with a force-password-change flag set.

---

### 4.4 Course Management

#### Creating a Course

1. Click **Courses** in the navigation, then click **New Course** (or use the Quick Action).
2. Enter the **Course Title** and a **Description**.
3. Set the **Category** and **Duration** (estimated learning time).
4. Add **Learning Outcomes** — the skills or knowledge the learner will gain.
5. Upload a **Course Thumbnail** image if desired.
6. Click **Save**. The course is saved as a draft.

> A draft course is not visible to learners. You must publish it when it is ready.

---

#### Adding Modules to a Course

1. Open the course from the Courses list.
2. Click **Add Module**.
3. Enter a **Module Title** and optional description.
4. Repeat to add all modules in order.
5. Drag and drop modules to reorder them.

---

#### Uploading Learning Materials

Within each module you can upload materials for learners to study.

1. Open the course and click on a module.
2. Click **Add Material**.
3. Select the material type: **File** (PDF, Word, video, etc.), **Link** (URL), or **Text** (written content).
4. Enter the title and upload the file or enter the URL/text content.
5. Click **Save Material**.
6. Repeat for all materials within the module.

> **Supported file types:** PDF, Word (.docx), PowerPoint (.pptx), MP4, and other common formats. Maximum upload size is configured by your system administrator.

---

#### Publishing a Course

A course must be published before learners can see it in the catalogue or be enrolled in it.

1. Open the course.
2. Confirm all modules and materials are complete.
3. Click **Publish Course**.
4. The course status changes from **Draft** to **Published**.

---

#### Editing a Course

1. Go to **Courses** and click the course title.
2. Click **Edit** to modify the title, description, outcomes, or thumbnail.
3. Click into any module to edit its materials.
4. Changes to a published course take effect immediately for all enrolled learners.

---

#### Archiving a Course

1. Open the course and click **Archive**.
2. Archived courses are removed from the learner catalogue but historical enrolment and completion records are retained.

---

### 4.5 Cohort Management

A cohort is a group of learners enrolled in a specific course, assigned to a trainer, with defined start and end dates.

#### Creating a Cohort

1. Click **Cohorts** in the navigation, then **New Cohort**.
2. Enter:
   - **Cohort Name** — e.g. "Sustainability Fundamentals — July 2026"
   - **Course** — select the published course this cohort covers
   - **Trainer** — assign one or more trainers
   - **Start Date** and **End Date**
   - **Maximum Capacity** (optional)
3. Click **Create Cohort**.

---

#### Enrolling Learners in a Cohort

**Individual enrolment:**
1. Open the cohort and click **Enrol Learner**.
2. Search for the learner by name or email.
3. Select the learner and click **Confirm Enrolment**.

**Bulk enrolment by CSV:**
1. Open the cohort and click **Bulk Enrol**.
2. Upload a CSV with one learner email per row.
3. The system will match emails to existing accounts and enrol them automatically.

**By self-enrolment token:**
1. Open the cohort and click **Generate Enrolment Link**.
2. Share the link with learners. Anyone with the link can enrol themselves without admin action.

---

#### Managing Cohort Enrolments

1. Open the cohort and go to the **Learners** tab.
2. You can view each learner's enrolment status, completion progress, and attendance.
3. To remove a learner, click the **Remove** button next to their name.
4. To update a learner's status (e.g. mark as withdrawn), click **Edit** on their enrolment row.

---

#### Document Requirements

Some cohorts may require learners to upload evidence documents before they can be considered complete.

1. Open the cohort and go to **Document Requirements**.
2. Click **Add Requirement** and describe the document needed.
3. Learners will see the requirement in their dashboard and can upload the document.
4. You can then review and approve or reject each submission.

---

### 4.6 Assessment Management

#### Creating an Assessment

1. Click **Assessments** in the navigation, then **New Assessment**.
2. Select the **Course** the assessment belongs to.
3. Enter the **Assessment Title** and **Instructions**.
4. Select the **Assessment Type**:
   - **Multiple Choice (MCQ)** — automatically scored
   - **Written** — requires trainer marking
   - **Short Answer** — requires trainer marking
   - **Mixed** — combines MCQ questions (auto-scored) and written/short-answer questions (trainer-marked)
5. Set a **Pass Mark** (percentage).
6. Set a **Time Limit** if required.
7. Click **Save**.

---

#### Adding Questions

**For MCQ questions:**
1. Click **Add Question**, select **Multiple Choice**.
2. Enter the question text.
3. Add answer options (minimum two).
4. Mark the correct answer(s).
5. Click **Save Question**.

**For written / short-answer questions:**
1. Click **Add Question**, select **Written** or **Short Answer**.
2. Enter the question text and optional marking guidance.
3. Click **Save Question**.

---

#### Publishing an Assessment

1. Open the assessment and click **Publish**.
2. Published assessments become available to learners enrolled in the associated course.

---

#### Viewing the Marking Queue

1. Click **Assessments** → **Marking Queue** (or use the Quick Action on the dashboard).
2. The queue shows all submissions with a **Pending Marking** status.
3. Filter by assessment using the dropdown at the top of the page.
4. Click a submission to open it and assign a mark.

---

### 4.7 Certificate Management

#### Issuing a Certificate

Certificates are issued automatically when a learner meets the pass mark and completes all required modules. You can also issue them manually:

1. Go to the learner's profile or the cohort's learner list.
2. Find the learner and click **Issue Certificate**.
3. Select the course/assessment the certificate is for.
4. Click **Confirm**.

---

#### Revoking a Certificate

1. Go to the learner's profile.
2. Find the certificate in the **Certificates** section.
3. Click **Revoke**, enter a reason, and confirm.

> Revoked certificates are flagged in the system but the training record is preserved.

---

### 4.8 Training Plans and Learning Paths

Learning paths bundle multiple courses into a structured programme.

#### Creating a Learning Path

1. Click **Paths** in the navigation, then **New Path**.
2. Enter a path **Title** and **Description**.
3. Add courses to the path in order by clicking **Add Course**.
4. Set whether each course is **required** or **optional**.
5. Click **Publish Path** when ready.

Learners enrolled in a path see their progress across all courses in the path from a single view.

---

### 4.9 Reports and Analytics

1. Click **Reports** in the navigation.
2. Available reports include:
   - **Subscriptions / Enrolments** — who is enrolled in what and their completion status
   - **Training Activity** — login activity, content access, and time-on-platform
   - **Certificate Report** — issued and expiring certificates
   - **Assessment Results** — scores and pass rates by course and learner
3. Apply filters (date range, cohort, course, learner) to narrow results.
4. Click **Export** to download a report as a CSV file.

---

### 4.10 System Settings

1. Click **Settings** in the navigation.
2. Settings available include:
   - **Organisation Name** — displayed throughout the system
   - **Minimum Attendance Threshold** — percentage required before a learner is considered to have attended (default 80%)
   - **Data Retention Period** — how long training records are kept (default 3 years)
   - **Maximum Upload Size** — limit on file uploads in MB (default 500 MB)

---

### 4.11 Notifications

The system sends automatic notifications for:
- New self-registration requests awaiting approval
- Assessment submissions pending marking
- Certificates nearing expiry
- Learner enrolment confirmations

Administrators receive notifications in the bell icon (top right) and, where configured, by email.

---

## 5. Trainer Guide

### 5.1 Trainer Responsibilities

As a trainer you are responsible for:

- Creating and managing training content for your assigned courses
- Uploading and organising learning materials
- Creating assessments and question banks
- Marking written and mixed assessment submissions
- Monitoring learner progress within your cohorts
- Reviewing skills evidence submitted by learners

---

### 5.2 The Trainer Dashboard

Your dashboard shows:

- **Pending Marking** — a count of submissions awaiting your review, with a direct link to the marking queue
- **Assigned Cohorts** — courses and cohorts you are responsible for
- **Recent Submissions** — the latest assessment submissions from your learners

---

### 5.3 Viewing Your Courses

1. Click **My Courses** (or **Dashboard**) to see courses assigned to you.
2. You will see courses you created yourself as well as published courses assigned to your cohorts.
3. Draft courses you created are marked **[DRAFT]** and are only visible to you and administrators.

---

### 5.4 Creating a Course

Trainers can create courses which are initially saved as drafts.

1. Click **Courses** → **New Course**.
2. Fill in the title, description, category, and duration.
3. Add learning outcomes.
4. Click **Save**. The course is saved as a draft.
5. Add modules and upload materials (see Section 4.4 for details — the process is the same for trainers).
6. When complete, click **Submit for Review** (or **Publish** if you have publish rights).

> Only administrators can publish a course. If you are a trainer without publish rights, an administrator will review and publish your course.

---

### 5.5 Uploading Learning Materials

1. Open the course and select the relevant module.
2. Click **Add Material** and select the type (File, Link, or Text).
3. Upload the file or enter the content.
4. Supported formats include PDF, Word, PowerPoint, and video files.
5. Click **Save Material**.

---

### 5.6 Creating Assessments

1. Click **Assessments** → **New Assessment**.
2. Select the course from the dropdown. You will see your own courses and all published courses.
3. Fill in the assessment details (title, instructions, type, pass mark, time limit).
4. Add questions appropriate to the assessment type.
5. Click **Publish** when ready.

For full step-by-step question creation instructions, see Section 4.6.

---

### 5.7 Marking Submitted Assessments

Written, short-answer, and the written section of mixed assessments must be manually marked.

#### Accessing the Marking Queue

1. Click the **Pending Marking** badge on your dashboard, or go to **Assessments** → **Marking Queue**.
2. The queue lists all submissions awaiting your review.
3. To filter by a specific assessment, use the **Assessment** dropdown at the top.

#### Alternatively, from an assessment detail page:
1. Go to **Assessments** and open the relevant assessment.
2. Click **View Marking Queue** to see only submissions for that assessment.

#### Marking a Submission

1. Click **Mark** on any submission in the queue.
2. Review the learner's answers.
3. For each written question, enter a mark and optional feedback comment.
4. For mixed assessments, the MCQ section is already auto-scored — you only mark the written section.
5. Enter an overall **Grade** and any **General Feedback** for the learner.
6. Click **Release Result**.

Once released, the learner can see their result, and if they have passed, a certificate is issued automatically.

---

### 5.8 Monitoring Learner Progress

1. From your dashboard or the **Cohorts** link, open one of your assigned cohorts.
2. The **Learners** tab shows each learner's progress:
   - Modules completed
   - Assessments submitted and their status
   - Overall completion percentage
3. Click a learner's name to view their full activity within that cohort.

---

### 5.9 Skills Review

Learners can submit evidence to claim skills linked to your courses.

1. Go to **Skills** in the navigation.
2. The **Review Queue** shows pending skill claims from learners in your cohorts.
3. Click **Review** on a claim to see the evidence uploaded.
4. Click **Approve** or **Reject**, adding a comment if needed.

---

### 5.10 Generating Reports

1. Go to **Reports** or the results section of your assigned cohort.
2. You can view assessment scores, completion rates, and attendance data for your learners.
3. Data is scoped to your own courses and cohorts only — you cannot see other trainers' data.

---

## 6. Learner Guide

### 6.1 Learner Responsibilities

As a learner you are responsible for:

- Completing assigned training within the required timescales
- Engaging with all learning materials in each module
- Submitting assessments honestly and to the best of your ability
- Keeping your profile information up to date
- Downloading and storing your certificates

---

### 6.2 The Learner Dashboard

After logging in you will see your personalised dashboard:

- **My Enrolled Courses** — courses you are currently enrolled in with progress indicators
- **Recent Notifications** — alerts about results released, certificates issued, and upcoming deadlines

---

### 6.3 Accessing Your Courses

#### From enrolment

When an administrator enrols you in a cohort, the course appears automatically in **My Courses**.

#### From the catalogue

1. Click **Catalogue** in the navigation to browse all available published courses.
2. Use the search bar or category filter to find relevant courses.
3. Click **Enrol** on any course to self-enrol (where self-enrolment is enabled).

---

### 6.4 Completing a Course

1. Click **My Courses** and select the course you want to study.
2. The course page shows all modules in order.
3. Click on a module to expand it and access the learning materials.
4. Work through each material — read documents, watch videos, or review content as provided.
5. Once you have reviewed a module's materials, it is marked as visited.
6. Progress through all modules before attempting the assessment.

---

### 6.5 Taking an Assessment

1. From the course page, scroll to the **Assessment** section and click **Start Assessment**.
2. Read the instructions carefully before beginning.
3. If a time limit applies, a countdown timer is shown at the top of the screen.

**Multiple Choice Questions:**
- Read each question and select the answer you believe is correct.
- You can navigate between questions using the **Previous** and **Next** buttons.
- Review your answers before submitting.

**Written / Short Answer Questions:**
- Type your response in the text box provided.
- There is no strict word limit unless stated in the question instructions.

**Mixed Assessments:**
- Complete the MCQ section first, then the written section.
- Both sections are submitted together.

4. Click **Submit Assessment** when you are ready to submit.
5. You will see a confirmation message. You cannot change your answers after submission.

---

### 6.6 Viewing Your Results

#### Multiple Choice only:
- Your result is available **immediately** after submission.
- Go to **Results** to see your score, the pass mark, and whether you passed or failed.

#### Written / Short Answer / Mixed:
- After submission your result shows as **Submitted — Awaiting Review**.
- Your trainer will mark your submission and release the result.
- You will receive a notification when your result is available.
- For mixed assessments, your MCQ partial score is shown while you wait for the written section to be marked.

---

### 6.7 Downloading Your Certificate

When you pass an assessment and meet all completion requirements:

1. A notification confirms your certificate has been issued.
2. Go to **Certificates** in the navigation.
3. Find the certificate and click **Download** to save it as a PDF.

---

### 6.8 Tracking Your Progress

**Training Record**
1. Click **Training Record** in the navigation.
2. This page shows every course you have completed, the date of completion, and the result.
3. It serves as your official training history within the organisation.

**Results**
1. Click **Results** to see all assessment submissions — past and current.
2. Each entry shows the assessment name, submission date, score, pass/fail status, and any feedback from your trainer.

---

### 6.9 Skills Portfolio

If your organisation uses skills tracking:

1. Click **Skills** in the navigation.
2. You will see skills linked to your enrolled courses.
3. To claim a skill, click **Claim**, complete the self-assessment, and upload any supporting evidence.
4. Your trainer will review and approve or reject your claim.

---

### 6.10 Learning Paths

1. Click **Paths** in the navigation.
2. You will see learning paths you are enrolled in.
3. A learning path shows all required courses in order and your overall progress across the path.
4. Complete courses in sequence — some paths may require you to complete earlier courses before accessing later ones.

---

### 6.11 Messages

1. Click **Messages** in the navigation.
2. You can send messages to your trainers and receive replies.
3. System notifications also appear here.

---

## 7. Observer & External Assessor Guide

### 7.1 Observer

Observers have read-only access to training data. This role is typically given to line managers or senior stakeholders who need visibility of training activity without being able to change anything.

**What observers can do:**
- View the dashboard summary of training activity
- Browse published courses
- View learner enrolment and completion data
- Access reports and exports

**What observers cannot do:**
- Create or edit any content
- Enrol or manage learners
- Mark assessments or issue certificates

To access the system as an observer, log in with your credentials. Your dashboard and navigation will automatically reflect observer-level access.

---

### 7.2 External Assessor

External assessors are invited to mark specific assessment submissions on behalf of the organisation.

1. Log in with the credentials provided by the administrator.
2. Go to **Assessments** → **Marking Queue**.
3. The queue shows only the submissions assigned to you.
4. Click **Mark** on a submission to review the learner's answers.
5. Enter marks and feedback for each question.
6. Click **Release Result** to finalise the marking.

You do not have access to any other part of the system.

---

## 8. End-to-End Workflow

This section walks through a complete real-world training cycle from setup through to certification.

### Step 1 — Administrator Creates a Course

1. Admin logs in and clicks **New Course** from the dashboard.
2. Enters the course title, description, and learning outcomes.
3. Saves the course as a draft.
4. Adds three modules to the course.

### Step 2 — Administrator Assigns a Trainer

1. Admin clicks **Cohorts** → **New Cohort**.
2. Selects the newly created course.
3. Assigns the trainer responsible for delivery.
4. Sets the cohort start and end dates.
5. Saves the cohort.

### Step 3 — Trainer Uploads Learning Materials

1. Trainer logs in and opens the assigned course.
2. Clicks into each module and uploads the relevant PDF, video, or written content.
3. Saves all materials.

### Step 4 — Trainer Creates an Assessment

1. Trainer goes to **Assessments** → **New Assessment**.
2. Selects the course and sets the type as **Mixed** (MCQ + written).
3. Adds 10 MCQ questions and 2 written questions.
4. Sets a pass mark of 70%.
5. Publishes the assessment.

### Step 5 — Administrator Publishes the Course and Enrols Learners

1. Admin opens the course and clicks **Publish Course**.
2. Opens the cohort and clicks **Enrol Learner** for each participant, or uses **Bulk Enrol** to upload a CSV of learner emails.

### Step 6 — Learners Complete the Training

1. Learners log in and see the course on their dashboard.
2. Each learner works through all three modules, reading the materials.
3. When ready, they click **Start Assessment** and complete all questions.
4. They click **Submit Assessment**.

### Step 7 — Trainer Reviews and Marks Submissions

1. Trainer sees a **Pending Marking: [number]** badge on their dashboard.
2. Clicks the badge to go to the marking queue.
3. Opens each submission, scores the written questions, and enters feedback.
4. Clicks **Release Result** for each submission.

### Step 8 — System Records Completion

- Learners who pass receive a notification: "Your result has been released."
- Their training record is automatically updated with the completion date and score.
- Completion is recorded in the cohort view for the trainer and administrator.

### Step 9 — Certificate is Issued

- For learners who meet the pass mark, a certificate is automatically generated.
- Learners receive a notification and can download the certificate from **Certificates**.

### Step 10 — Administrator Reviews Reporting

1. Admin goes to **Reports** → **Subscriptions**.
2. Filters by the cohort to see all learner completion statuses.
3. Exports the report as CSV for compliance records.
4. Reviews **Expiring Certs** on the dashboard to plan renewal training.

---

## 9. Additional Features

### 9.1 Notifications

The notification bell (top right) shows unread alerts. Notifications are sent for:

| Event | Recipient |
|---|---|
| New self-registration request | Administrator |
| Learner enrolled in a cohort | Learner |
| Assessment submitted for marking | Trainer |
| Result released | Learner |
| Certificate issued | Learner |
| Certificate nearing expiry | Administrator |
| Skill claim submitted | Trainer |
| Document submitted for review | Administrator / Trainer |

---

### 9.2 File Uploads

- Supported types: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), images (JPG, PNG), video (MP4), and audio.
- Maximum file size is set by your administrator (default 500 MB).
- Files are stored securely and only accessible to users with appropriate permissions.

---

### 9.3 Certificates

- Certificates are issued automatically on passing an assessment.
- They can be downloaded as PDF from the **Certificates** page.
- Administrators can issue certificates manually and revoke them with a reason.
- Expiry tracking alerts administrators when certificates are nearing their renewal date.

---

### 9.4 Compliance and GDPR

- All users must accept the GDPR consent statement on first login.
- Consent dates are recorded and auditable.
- Training records are retained for the period specified in Settings (default 3 years).
- Personal data is not used for any purpose beyond training administration, assessment recording, and certificate issuance.

---

### 9.5 Question Bank

Trainers and administrators can build a reusable bank of assessment questions.

1. Go to **Assessments** → **Question Bank**.
2. Click **Add Question** to create a question for reuse across assessments.
3. When creating an assessment, click **Import from Bank** to pull in existing questions.

---

## 10. Frequently Asked Questions

**Q: I cannot log in. What should I do?**
Check that you are using the correct email or username and that Caps Lock is not on. After five failed attempts your account is locked for 30 minutes. Contact your administrator if you need access sooner.

**Q: I have forgotten my password. How do I reset it?**
Click **Forgot password?** on the login page and enter your email address. You will receive a reset link by email.

**Q: I did not receive the GDPR or password setup page. How do I access it?**
Navigate directly to the LMS URL and log in. If your account requires setup, you will be redirected automatically. If not, contact your administrator to re-enable the flag.

**Q: My assessment result shows "Awaiting Review". When will I get my result?**
Written and mixed assessments must be marked by your trainer. Contact your trainer if you have been waiting more than your organisation's standard turnaround time.

**Q: Can I retake an assessment?**
Retakes are at the administrator's discretion. Contact your administrator or trainer if you need a retake.

**Q: Where is my certificate?**
Go to **Certificates** in the navigation. If you passed the assessment and completed all required modules it should be there. If not, contact your administrator.

**Q: Can I see my full training history?**
Yes. Click **Training Record** in the navigation to see all completed training.

**Q: I uploaded the wrong file to a module. Who can fix this?**
Trainers can replace materials within their courses. Administrators can edit all course materials. Contact either to have the file replaced.

**Q: The course I need is not in the catalogue. What should I do?**
Contact your administrator. The course may not yet be published, or you may need to be enrolled in a specific cohort.

**Q: Can I download the learning materials to read offline?**
PDF and document materials can be downloaded from the course page. Video content must be streamed online.

---

## 11. Troubleshooting Guide

### Administrators

| Problem | Solution |
|---|---|
| User cannot log in | Check the account is active and not locked. Edit the user and reset their password if needed. |
| Course not appearing in catalogue | Check the course status is **Published**, not Draft. |
| Bulk CSV import fails | Check the CSV matches the template exactly. Remove special characters from names. Ensure emails are unique. |
| Certificate not generated after pass | Check the learner's result was released by the trainer (not still Pending Marking). Check the pass mark setting on the assessment. |
| Enrolment requests not showing | Go to Users and filter by Pending status. |
| Report shows no data | Check the date range and cohort filter. Ensure learners have been enrolled and have submitted assessments. |
| Navigation link shows 404 | Contact your system administrator. Some links may point to routes that have been updated. |

---

### Trainers

| Problem | Solution |
|---|---|
| Cannot see a course in the assessment dropdown | Only your own courses and published courses appear. If the course is a draft by another trainer it will not show. |
| Marking queue is empty | No submissions with Pending Marking status exist for your assigned courses. Check that learners have submitted. |
| Cannot release a result | Ensure you have entered a mark for all written questions. The release button is disabled until all questions are marked. |
| Learner progress not updating | Progress updates on module access and assessment submission. Ask the learner to confirm they clicked through the module materials. |
| File upload fails | Check the file size is within the system limit. Try a different file format if the type is unsupported. |

---

### Learners

| Problem | Solution |
|---|---|
| Course not appearing in My Courses | Confirm with your administrator that you have been enrolled in a cohort for that course. |
| Cannot start an assessment | Check you have worked through the required modules. Some assessments are locked until modules are complete. |
| Assessment submitted but no confirmation | Check your **Results** page. If the submission is not listed, try submitting again — the first attempt may not have gone through. |
| Result shows wrong score | Contact your trainer. For MCQ, scores are calculated automatically, but your trainer can review and correct if needed. |
| Certificate not available after passing | Allow up to 24 hours. If still missing, contact your administrator. |
| Cannot download a certificate | Try a different browser. Ensure your browser allows PDF downloads. |
| Password not accepted on first login | Ensure your new password is at least 8 characters and includes uppercase, lowercase, a number, and a symbol. |

---

## 12. Best Practices

### For Administrators

- **Create cohorts before enrolling learners.** Learners should be enrolled into cohorts, not just courses, so trainer assignment and scheduling are tracked.
- **Use bulk CSV import for groups of five or more.** This saves time and reduces manual errors.
- **Publish courses only when they are fully complete.** Learners can access a course immediately after it is published.
- **Check the Expiring Certs dashboard card monthly.** Proactively arrange renewal training before certificates expire.
- **Review enrolment requests promptly.** Learners waiting for approval cannot access any training in the meantime.
- **Set a clear naming convention for cohorts.** For example: `[Course Name] — [Month Year]`.
- **Export reports monthly** and save them to a compliance folder as an audit record.

### For Trainers

- **Upload materials before creating the assessment.** Learners should be able to study before they are assessed.
- **Use mixed assessments for complex topics.** MCQ handles recall well; written questions test understanding and application.
- **Provide feedback on every marked submission.** Learners value specific, actionable feedback even when they pass.
- **Check the marking queue daily during an active cohort.** Learners cannot receive their certificate until their result is released.
- **Use the Question Bank** for questions you reuse across multiple assessments to save time and maintain consistency.
- **Preview assessments before publishing** to confirm questions and instructions read correctly from the learner's perspective.

### For Learners

- **Complete all modules before attempting the assessment.** The materials are there to prepare you — use them.
- **Download your certificates as soon as they are issued.** Keep a personal copy in case you need to share it externally.
- **Check your Training Record periodically.** It is your official record of completed training within the organisation.
- **Read assessment instructions carefully.** Note the time limit and pass mark before you begin.
- **Submit your assessment only when you are ready.** You cannot change your answers after submission.
- **Contact your trainer for feedback** if your result is released without written comments.

---

## 13. Quick Start Guides

### Quick Start — Administrator (5 Steps)

| Step | Action | Where |
|---|---|---|
| 1 | Log in and review the dashboard for any pending actions | Dashboard |
| 2 | Create a new user and assign the correct role | Users → Add User |
| 3 | Create a course, add modules, and upload materials | Courses → New Course |
| 4 | Create a cohort, assign a trainer, and enrol learners | Cohorts → New Cohort |
| 5 | Monitor completion and export reports | Reports |

---

### Quick Start — Trainer (5 Steps)

| Step | Action | Where |
|---|---|---|
| 1 | Log in and check your dashboard for pending marking | Dashboard |
| 2 | Open your assigned course and add or update learning materials | My Courses → [Course] |
| 3 | Create or update an assessment for your course | Assessments → New Assessment |
| 4 | Mark any submissions in the Pending Marking queue | Assessments → Marking Queue |
| 5 | Review learner progress in your cohort | Dashboard → [Cohort] → Learners |

---

### Quick Start — Learner (5 Steps)

| Step | Action | Where |
|---|---|---|
| 1 | Log in and complete the Account Setup Wizard if prompted | Auto-redirect on first login |
| 2 | Open your enrolled course and work through all modules | My Courses → [Course] |
| 3 | Take and submit the assessment when ready | Course page → Start Assessment |
| 4 | Check your result once your trainer has released it | Results |
| 5 | Download your certificate if you passed | Certificates |

---

*This guide covers all functionality confirmed present and working in the PLP LMS as of June 2026. For system support or to report an issue, contact your system administrator.*

---

**PL Projects Ltd — B Corp Certified Project Management Consultancy**
*© 2026 PL Projects Ltd. All rights reserved.*
