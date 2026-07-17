from fastapi import FastAPI

app = FastAPI(title="Uraan AI")

@app.get("/")
def root():
    return {"message": "Welcome to Uraan AI 🚀"}

@app.get("/health")
def health():
    return {"status": "healthy"}