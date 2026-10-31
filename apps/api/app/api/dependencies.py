from fastapi import Depends
from fastapi.security import HTTPBearer

from app.core.monitoring import identify
from app.core.security import verify_token

security = HTTPBearer()


def get_current_user(credentials=Depends(security)):
    user = verify_token(credentials.credentials)

    # Error reports say whose request failed (by account id only).
    identify(user.id)

    return user
