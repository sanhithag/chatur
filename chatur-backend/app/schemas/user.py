from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class SchoolCreate(BaseModel):
    name: str
    code: str


class SchoolResponse(BaseModel):
    id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # super_admin, admin, teacher, student, parent
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_lang: str = "en"
    school_id: Optional[str] = None
    # For students
    grade: Optional[int] = None
    section: Optional[str] = None
    roll_no: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_lang: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_lang: str
    is_active: bool
    school_id: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
