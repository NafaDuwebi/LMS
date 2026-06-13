from itsdangerous import URLSafeTimedSerializer
from fastapi import Request, HTTPException
from starlette.responses import PlainTextResponse
from config import SECRET_KEY

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="csrf-token")


def generate_csrf_token() -> str:
    import secrets
    return serializer.dumps(secrets.token_urlsafe(32))


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        serializer.loads(token, max_age=max_age)
        return True
    except Exception:
        return False


async def csrf_middleware(request, call_next):
    """Sets request.state.csrf_token and consumes flash for templates."""
    token = request.cookies.get("csrf_token")
    if not token or not validate_csrf_token(token):
        token = generate_csrf_token()

    request.state.csrf_token = token
    request.state.flash_msg = request.session.pop("_flash", None)

    response = await call_next(request)

    refresh = getattr(request.state, "refresh_token", None)
    if refresh:
        import os
        response.set_cookie(
            key="access_token",
            value=refresh,
            httponly=True,
            max_age=3600,
            path="/",
            secure=os.getenv("ENV", "development") == "production",
        )

    # Set csrf cookie if not present
    if not request.cookies.get("csrf_token"):
        response.set_cookie(
            key="csrf_token",
            value=token,
            httponly=True,
            max_age=3600,
            path="/",
        )

    return response


async def validate_csrf(request: Request):
    """Dependency: validates csrf_token form field against cookie token."""
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    form_token = request.headers.get("x-csrftoken")
    if not form_token:
        try:
            form = await request.form()
            form_token = form.get("csrf_token")
        except Exception:
            pass

    if not form_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    try:
        serializer.loads(form_token, max_age=3600)
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    cookie_token = request.cookies.get("csrf_token")
    # Fallback to state token (freshly set by middleware if no cookie yet)
    expected = cookie_token or request.state.csrf_token
    import secrets
    if not secrets.compare_digest(form_token, expected):
        raise HTTPException(status_code=403, detail="CSRF token mismatch")
