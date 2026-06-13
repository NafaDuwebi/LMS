from locust import HttpUser, task, between
import re


class LMSUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:8000"

    def on_start(self):
        """Login with a learner account."""
        resp = self.client.get("/auth/login")
        csrf = self.client.cookies.get("csrf_token", "")
        self.client.post(
            "/auth/login",
            data={"username": "learner1@example.com", "password": "Learner1234!", "csrf_token": csrf},
        )

    @task(3)
    def view_dashboard(self):
        self.client.get("/dashboard")

    @task(2)
    def view_learner_courses(self):
        self.client.get("/learner/courses")

    @task(2)
    def view_assessments(self):
        self.client.get("/assessments")
