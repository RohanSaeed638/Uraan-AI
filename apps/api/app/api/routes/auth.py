from fastapi import APIRouter, HTTPException

from app.schemas.auth import LoginRequest
from app.schemas.auth import RegisterRequest

from app.services.auth_service import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(request: RegisterRequest):

    try:

        result = auth_service.register(
            request.email,
            request.password,
            request.full_name,
        )

        return {
            "success": True,
            "message": "Registration successful. Check your email.",
            "user": result.user,
        }

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/login")
def login(request: LoginRequest):

    try:

        result = auth_service.login(
            request.email,
            request.password,
        )

        return {
            "success": True,
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": result.user,
        }

    except Exception as e:
        raise HTTPException(401, str(e))


@router.post("/logout")
def logout():

    auth_service.logout()

    return {
        "success": True
    }