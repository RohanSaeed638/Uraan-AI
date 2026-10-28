from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class RegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=8)

    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr

    password: str


class AuthResponse(BaseModel):
    access_token: str | None = None

    refresh_token: str | None = None

    message: str

    user: dict | None = None


class CurrentUser(BaseModel):
    id: UUID
    email: str | None = None    