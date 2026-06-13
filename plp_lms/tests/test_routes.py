"""Route accessibility and permission tests."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

import pytest
from fastapi.testclient import TestClient
from main import app


def _get_csrf(client):
    for cookie in client.cookies.jar:
        if cookie.name == "csrf_token":
            return cookie.value
    return None


def _login(client, email, password):
    """Login and return access token."""
    r = client.get("/auth/login")
    csrf = _get_csrf(client)
    r = client.post("/auth/login", data={
        "username": email, "password": password, "csrf_token": csrf or "",
    }, follow_redirects=False)
    assert r.status_code == 302, f"Login failed for {email}: {r.status_code}"
    for cookie in client.cookies.jar:
        if cookie.name == "access_token":
            return cookie.value
    sc = r.headers.get("set-cookie", "")
    m = re.search(r"access_token=([^;]+)", sc)
    return m.group(1) if m else ""


class TestAdminRoutes:
    def test_admin_users_page(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/admin/users", cookies={"access_token": token})
        assert r.status_code == 200

    def test_admin_settings_page(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/admin/settings", cookies={"access_token": token})
        assert r.status_code == 200

    def test_trainer_cannot_access_admin(self, client):
        token = _login(client, "trainer@plprojects.co.uk", "Trainer1234!")
        r = client.get("/admin/users", cookies={"access_token": token})
        assert r.status_code == 403

    def test_learner_cannot_access_admin(self, client):
        token = _login(client, "learner1@example.com", "Learner1234!")
        r = client.get("/admin/users", cookies={"access_token": token})
        assert r.status_code == 403


class TestDashboardRoutes:
    def test_admin_dashboard(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/dashboard", cookies={"access_token": token})
        assert r.status_code == 200

    def test_trainer_dashboard(self, client):
        token = _login(client, "trainer@plprojects.co.uk", "Trainer1234!")
        r = client.get("/dashboard", cookies={"access_token": token})
        assert r.status_code == 200

    def test_learner_dashboard(self, client):
        token = _login(client, "learner1@example.com", "Learner1234!")
        r = client.get("/dashboard", cookies={"access_token": token})
        assert r.status_code == 200

    def test_observer_dashboard(self, client):
        token = _login(client, "observer@plprojects.co.uk", "Observer1234!")
        r = client.get("/dashboard", cookies={"access_token": token})
        assert r.status_code == 200

    def test_no_auth_redirects(self, client):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code == 302


class TestCourseRoutes:
    def test_courses_list(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/courses", cookies={"access_token": token})
        assert r.status_code == 200


class TestCohortRoutes:
    def test_cohorts_list(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/cohorts", cookies={"access_token": token})
        assert r.status_code == 200


class TestReportsRoutes:
    def test_reports_page(self, client):
        token = _login(client, "admin@plprojects.co.uk", "Admin1234!")
        r = client.get("/reports", cookies={"access_token": token})
        assert r.status_code == 200

    def test_reports_accessible_by_trainer(self, client):
        token = _login(client, "trainer@plprojects.co.uk", "Trainer1234!")
        r = client.get("/reports", cookies={"access_token": token})
        assert r.status_code == 200

    def test_reports_accessible_by_observer(self, client):
        token = _login(client, "observer@plprojects.co.uk", "Observer1234!")
        r = client.get("/reports", cookies={"access_token": token})
        assert r.status_code == 200


class TestNotificationRoutes:
    def test_notifications(self, client):
        token = _login(client, "learner1@example.com", "Learner1234!")
        r = client.get("/notifications", cookies={"access_token": token})
        assert r.status_code == 200


class TestAssessorRoutes:
    def test_assessor_dashboard(self, client):
        token = _login(client, "assessor@plprojects.co.uk", "Assessor1234!")
        r = client.get("/external-assessor/dashboard", cookies={"access_token": token})
        assert r.status_code == 200

    def test_assessor_skills_review(self, client):
        token = _login(client, "assessor@plprojects.co.uk", "Assessor1234!")
        r = client.get("/external-assessor/skills", cookies={"access_token": token})
        assert r.status_code == 200

    def test_learner_cannot_access_assessor(self, client):
        token = _login(client, "learner1@example.com", "Learner1234!")
        r = client.get("/external-assessor/dashboard", cookies={"access_token": token})
        assert r.status_code == 403


class TestPublicRoutes:
    def test_certificate_verify_page(self, client):
        r = client.get("/certificates/verify/PLP-2026-0001")
        assert r.status_code in (200, 404)

    def test_home_redirects_to_login(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 302


class TestErrorHandling:
    def test_404_returns_template(self, client):
        r = client.get("/nonexistent-route", follow_redirects=False)
        assert r.status_code == 404

    def test_403_for_unauthorized(self, client):
        token = _login(client, "learner1@example.com", "Learner1234!")
        r = client.get("/admin/users", cookies={"access_token": token})
        assert r.status_code == 403
