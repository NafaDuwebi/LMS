class RedirectException(Exception):
    def __init__(self, url: str, status_code: int = 302):
        self.url = url
        self.status_code = status_code


class GDPRConsentRequired(RedirectException):
    def __init__(self):
        super().__init__("/auth/gdpr-consent")


class PasswordChangeRequired(RedirectException):
    def __init__(self):
        super().__init__("/auth/change-password")
