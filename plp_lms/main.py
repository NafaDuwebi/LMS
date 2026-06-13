import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("plp_lms")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from database import init_db
from services.csrf_middleware import csrf_middleware, validate_csrf
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config import MAX_UPLOAD_MB, SECRET_KEY
from services.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    from config import SECRET_KEY; assert SECRET_KEY and len(SECRET_KEY) >= 64, "FATAL: SECRET_KEY env var must be set to a 64+ character random string"
    init_db()
    os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "certificates"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "exports"), exist_ok=True)
    from services.scheduler_service import scheduler, deliver_reports_task, flag_retention_records
    scheduler.start()
    scheduler.add_job(deliver_reports_task, 'cron', hour='*', minute='0')
    scheduler.add_job(flag_retention_records, 'cron', hour='2', minute='0')
    yield


app = FastAPI(title="PLP Learning Management System", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    from template_utils import templates
    return templates.TemplateResponse("base.html", {"request": request, "error": "Page not found"}, status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Internal server error: %s", exc)
    from template_utils import templates
    return templates.TemplateResponse("base.html", {"request": request, "error": "An internal error occurred. Please try again."}, status_code=500)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            logger.warning("%s %s -> %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as exc:
        logger.exception("Unhandled error processing %s %s", request.method, request.url.path)
        raise

MAX_BODY_BYTES = MAX_UPLOAD_MB * 1024 * 1024


@app.middleware("http")
async def max_body_size_middleware(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BODY_BYTES:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=413, content={"detail": f"Request body exceeds maximum size of {MAX_UPLOAD_MB}MB"})
    return await call_next(request)


app.middleware("http")(csrf_middleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if os.getenv("ENV", "development") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'"
    return response

if os.getenv("ENV", "development") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(","))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

from datetime import datetime
from template_utils import templates
templates.env.globals["now"] = datetime.utcnow


from routers import auth, admin, trainer, learner, courses, cohorts, assessments, attendance, certificates as cert_router, reports, notifications, dashboard, v2_1, observer, external_assessor

app.include_router(auth.router, dependencies=[Depends(validate_csrf)])
app.include_router(dashboard.router)
app.include_router(admin.router, dependencies=[Depends(validate_csrf)])
app.include_router(trainer.router, dependencies=[Depends(validate_csrf)])
app.include_router(learner.router, dependencies=[Depends(validate_csrf)])
app.include_router(courses.router, dependencies=[Depends(validate_csrf)])
app.include_router(cohorts.router, dependencies=[Depends(validate_csrf)])
app.include_router(assessments.router, dependencies=[Depends(validate_csrf)])
app.include_router(attendance.router, dependencies=[Depends(validate_csrf)])
app.include_router(cert_router.router, dependencies=[Depends(validate_csrf)])
app.include_router(reports.router)
app.include_router(notifications.router, dependencies=[Depends(validate_csrf)])
app.include_router(v2_1.router, dependencies=[Depends(validate_csrf)])
app.include_router(observer.router, dependencies=[Depends(validate_csrf)])
app.include_router(external_assessor.router, dependencies=[Depends(validate_csrf)])


@app.get("/")
def home(request: Request):
    return RedirectResponse(url="/auth/login", status_code=302)


if __name__ == "__main__":
    import uvicorn
    import os
    is_dev = os.getenv("ENV", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=is_dev, workers=1 if is_dev else int(os.getenv("WORKERS", "4")))
