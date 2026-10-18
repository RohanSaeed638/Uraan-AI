from fastapi import FastAPI
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
from app.core.exceptions import global_exception_handler
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Uraan AI")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(roadmap_router)
app.include_router(task_router)
app.include_router(learning_unit_router)
app.include_router(dashboard_router)
app.include_router(learning_router)
app.include_router(progress_router)
app.include_router(projects_router)
app.include_router(quizzes_router)
app.include_router(settings_router)
app.include_router(mentor_router)
app.include_router(gamification_router)
app.include_router(leaderboard_router)
app.include_router(notifications_router)
app.include_router(calendar_router)
app.include_router(documents_router)
app.include_router(portfolio_router)
app.include_router(interviews_router)
app.include_router(account_router)
app.add_exception_handler(
    Exception,
    global_exception_handler
)

@app.get("/")
def root():
    return {"message": "Welcome to Uraan AI 🚀"}

@app.get("/health")
def health():
    return {"status": "healthy"}

