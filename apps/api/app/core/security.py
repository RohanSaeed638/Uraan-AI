from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from app.core.config import settings

security = HTTPBearer()

async def get_current_user(credentials=Depends(security)):
    token = credentials.credentials

    # Verify JWT with Supabase

    # Extract user_id

    # Return authenticated user


def verify_token(token):

    payload = jwt.decode(

        token,

        settings.SUPABASE_JWT_SECRET,

        algorithms=["HS256"]

    )

    return payload    