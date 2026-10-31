from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.roadmap import router as roadmap_router
from app.api.routes.task import router as task_router
from app.api.routes.learning_unit import router as learning_unit_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.learning import router as learning_router
from app.api.routes.progress import router as progress_router
from app.api.routes.projects import router as projects_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.settings import router as settings_router
from app.api.routes.mentor import router as mentor_router
from app.api.routes.gamification import router as gamification_router
from app.api.routes.leaderboard import router as leaderboard_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.calendar import router as calendar_router
from app.api.routes.documents import router as documents_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.interviews import router as interviews_router
from app.api.routes.account import router as account_router
from app.api.routes.careers import router as careers_router
from app.api.routes.library import router as library_router
from app.api.routes.achievements import router as achievements_router
from app.api.routes.email import router as email_router
from app.api.routes.admin import public as announcements_router, router as admin_router
from app.core.config import settings
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.monitoring import init_sentry
from app.core.observability import RequestContextMiddleware, configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import SessionLocal
from fastapi.middleware.cors import CORSMiddleware


configure_logging()
init_sentry()

app = FastAPI(title="Uraan AI", version="1")

# Added last = outermost: the request id is set before anything else runs, so
# even a CORS or error response carries it.
# Innermost first: the limit runs inside CORS (a 429 still carries CORS headers
# the browser can read) and inside the request id (it is in the 429 body).
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
app.add_middleware(RequestContextMiddleware)

# Everything the web app calls lives under /api/v1, so a breaking change can
# ship as /api/v2 next to it. Health checks stay at the root.
api_v1 = APIRouter(prefix="/api/v1")

for router in (
    auth_router, profile_router, roadmap_router, task_router, learning_unit_router,
    dashboard_router, learning_router, progress_router, projects_router, quizzes_router,
    settings_router, mentor_router, gamification_router, leaderboard_router,
    notifications_router, calendar_router, documents_router, portfolio_router,
    interviews_router, account_router, careers_router, library_router,
    achievements_router, email_router, admin_router, announcements_router,
):
    api_v1.include_router(router)

app.include_router(api_v1)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/")
def root():
    return {"message": "Welcome to Uraan AI 🚀"}


@app.get("/health")
def health():
    """Is the process up? Cheap: for a load balancer's frequent checks."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def ready():
    """Can it serve? Also checks the database, so a deploy that cannot reach it
    is not sent traffic."""
    try:
        async with SessionLocal() as db:
            await db.execute(text("select 1"))
    except Exception:
        return JSONResponse({"status": "unavailable", "database": "error"}, status_code=503)

    return {"status": "ready", "database": "ok"}
