from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.core.exceptions import global_exception_handler
app = FastAPI(title="Uraan AI")

app.include_router(auth_router)

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

