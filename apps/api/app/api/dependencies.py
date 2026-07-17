from app.core.database import SessionLocal
from fastapi import Depends
from fastapi.security import HTTPBearer
from core.security import verify_token
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def get_current_user(

    credentials=Depends(security)

):

    return verify_token(

        credentials.credentials

    )        