from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.roadmap import router as roadmap_router
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

