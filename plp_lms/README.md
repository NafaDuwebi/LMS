# PLP Learning Management System

A desktop/local-web Learning Management System (LMS) for PL Projects Ltd (PLP), a UK-based B Corp certified project management consultancy.

## Features

- **Role-based access**: Super Admin, Trainer, Learner, Observer
- **Course Management**: Create/edit courses, modules, materials with reordering
- **Cohort Management**: Create cohorts, enrol learners (manual/bulk CSV), waiting list
- **Assessment Engine**: MCQ auto-marking, written submissions for trainer marking, practical sign-off
- **Attendance Tracking**: Session attendance register with threshold enforcement
- **Progress Tracking**: Module-by-module completion tracking
- **Digital Certificates**: Auto-generated PDF certificates with unique numbers and public verification
- **Universal Training Record**: Combined record of LMS completions and external training
- **Reporting**: Built-in reports (cohort summary, compliance, certificate register)
- **Notifications**: In-app notification system
- **GDPR Compliance**: Consent recording, data retention, Subject Access Request export
- **Audit Log**: Full audit trail of all significant actions

## Quick Start

```bash
# Clone and enter the directory
cd plp_lms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (optional for local dev)

# Initialize database and seed data
python -c "from database import init_db; init_db()"
python seed_data.py

# Start the server
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

## Default Accounts

| Role | Email | Password |
|---|---|---|
| Super Admin | admin@plprojects.co.uk | Admin1234! |
| Trainer | trainer@plprojects.co.uk | Trainer1234! |
| Observer | observer@plprojects.co.uk | Observer1234! |
| Learner 1 | learner1@example.com | Learner1234! |
| Learner 2 | learner2@example.com | Learner1234! |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLite via SQLAlchemy ORM
- **Frontend**: Jinja2 templates + TailwindCSS (CDN)
- **Auth**: Session-based login (bcrypt hashed passwords, JWT in HTTP-only cookies)
- **PDF**: ReportLab for certificate generation
- **Charts**: Plotly (learner progress, trainer dashboards)

## Project Structure

```
plp_lms/
├── main.py              # Application entry point
├── config.py            # Configuration from .env
├── database.py          # Database setup
├── models/              # SQLAlchemy ORM models
├── routers/             # FastAPI route handlers
├── services/            # Business logic
├── templates/           # Jinja2 templates
├── static/              # Static assets
├── uploads/             # Uploaded files
├── certificates/        # Generated certificates
├── exports/             # Exported reports
├── seed_data.py         # Database seed script
└── requirements.txt     # Python dependencies
```

## License

PL Projects Ltd - Internal Use
