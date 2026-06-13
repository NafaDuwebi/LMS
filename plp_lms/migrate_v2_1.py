"""PLP LMS v2.1 Migration — adds new tables and columns safely."""
from database import init_db, engine, Base
import models  # noqa — registers all models with Base

def migrate():
    print("Running v2.1 migration...")
    init_db()
    print("All new tables created (existing tables preserved).")

if __name__ == "__main__":
    migrate()
