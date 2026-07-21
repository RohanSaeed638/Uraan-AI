from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError,jwt
from app.core.config import settings
from app.schemas.auth import CurrentUser
from .supabase import supabase
security = HTTPBearer()

async def get_current_user(credentials=Depends(security)):
    token = credentials.credentials

    # Verify JWT with Supabase

    # Extract user_id

    # Return authenticated user


def verify_token(token: str) -> dict:
    try:
        # payload = jwt.decode(
        #         token,
        #         settings.SUPABASE_JWT_SECRET,
        #         algorithms=["HS256"],
        #         audience="authenticated",  # if your Supabase project uses audience
        #     )
        # return CurrentUser(
        #         id=payload["sub"],
        #         email=payload.get("email"),
        #     )
    
        user = supabase.auth.get_user(token)

        if not user.user:
            raise HTTPException(401)

        return user.user

    except JWTError:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
    