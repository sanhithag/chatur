from typing import Optional
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str
    school_code: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"  # student, teacher, parent
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_lang: str = "en"
    # For students
    grade: Optional[int] = 9
    section: Optional[str] = "A"
    school_code: Optional[str] = None
    # For parents (optional linked student username)
    linked_student_username: Optional[str] = None


class UserSummary(BaseModel):
    id: str
    username: str
    role: str
    preferred_lang: str
    name: Optional[str] = None
    email: Optional[str] = None
    school_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSummary


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    username_or_email: str


class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

