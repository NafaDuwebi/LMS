"""Auth route tests."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from main import app


def _get_csrf(client):
    """Extract csrf_token from the test client's cookie jar."""
    for cookie in client.cookies.jar:
        if cookie.name == "csrf_token":
            return cookie.value
    return None


def _login_post(client, username, password):
    """POST login with CSRF token from cookie."""
    csrf = _get_csrf(client)
    if not csrf:
        # GET first to set the cookie
        client.get("/auth/login")
        csrf = _get_csrf(client)
    return client.post("/auth/login", data={
        "username": username,
        "password": password,
        "csrf_token": csrf or "",
    }, follow_redirects=False)


class TestLoginPage:
    def test_login_page_loads(self, client):
        r = client.get("/auth/login")
        assert r.status_code == 200

    def test_register_page_loads(self, client):
        r = client.get("/auth/register")
        assert r.status_code == 200

    def test_login_success_redirects(self, client):
        r = _login_post(client, "admin@plprojects.co.uk", "Admin1234!")
        assert r.status_code == 302, f"Expected 302, got {r.status_code}"
        assert "access_token" in r.headers.get("set-cookie", "")

    def test_login_bad_password_returns_form(self, client):
        r = _login_post(client, "admin@plprojects.co.uk", "wrongpassword")
        assert r.status_code in (200, 401)

    def test_gdpr_consent_accessible(self, client):
        client.get("/auth/login")  # get csrf cookie
        r = client.get("/auth/gdpr-consent")
        assert r.status_code == 200
