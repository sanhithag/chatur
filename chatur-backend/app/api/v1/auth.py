from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.deps import get_current_user, get_db
from app.models.student import ParentChildLink, StudentProfile
from app.models.user import AuthToken, School, UserAccount
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserSummary,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserAccount).where(UserAccount.username == credentials.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive",
        )

    if credentials.school_code:
        school_stmt = select(School).where(School.code == credentials.school_code)
        school_res = await db.execute(school_stmt)
        school = school_res.scalar_one_or_none()
        if not school or user.school_id != school.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not belong to specified school",
            )

    token_payload = {
        "sub": user.id,
        "role": user.role,
        "school_id": user.school_id,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    # Record refresh token in database
    auth_token = AuthToken(
        user_id=user.id,
        token=refresh_token,
        token_type="refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        is_revoked=False,
    )
    db.add(auth_token)

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserSummary(
            id=user.id,
            username=user.username,
            role=user.role,
            preferred_lang=user.preferred_lang,
            name=user.name,
            email=user.email,
            school_id=user.school_id,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh",
            )
        user_id = decoded.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check token record in database
    stmt = select(AuthToken).where(
        AuthToken.token == payload.refresh_token,
        AuthToken.is_revoked.is_(False),
    )
    res = await db.execute(stmt)
    token_record = res.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked or is invalid",
        )

    now = datetime.now(timezone.utc)
    # Check expiry (make sure comparison is timezone-aware)
    exp = token_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Fetch user
    u_stmt = select(UserAccount).where(UserAccount.id == user_id)
    u_res = await db.execute(u_stmt)
    user = u_res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token({
        "sub": user.id,
        "role": user.role,
        "school_id": user.school_id,
    })

    return TokenResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    logout_req: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    if logout_req.refresh_token:
        stmt = select(AuthToken).where(AuthToken.token == logout_req.refresh_token)
        res = await db.execute(stmt)
        token_record = res.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True
            await db.commit()
    else:
        # Revoke all active refresh tokens for this user
        stmt = select(AuthToken).where(
            AuthToken.user_id == current_user.id,
            AuthToken.is_revoked.is_(False),
        )
        res = await db.execute(stmt)
        tokens = res.scalars().all()
        for tok in tokens:
            tok.is_revoked = True
        await db.commit()

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserAccount = Depends(get_current_user),
):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.email is not None:
        # Check uniqueness if changed
        if payload.email != current_user.email:
            stmt = select(UserAccount).where(UserAccount.email == payload.email, UserAccount.id != current_user.id)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=400, detail="Email is already taken")
        current_user.email = payload.email
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.preferred_lang is not None:
        current_user.preferred_lang = payload.preferred_lang

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    req_role = req.role.lower().strip()
    if req_role not in ("student", "teacher", "parent"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: student, teacher, parent",
        )

    # Check username uniqueness
    u_stmt = select(UserAccount).where(UserAccount.username == req.username.strip())
    existing_u = (await db.execute(u_stmt)).scalar_one_or_none()
    if existing_u:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    # Check email uniqueness if provided
    if req.email and req.email.strip():
        e_stmt = select(UserAccount).where(UserAccount.email == req.email.strip())
        existing_e = (await db.execute(e_stmt)).scalar_one_or_none()
        if existing_e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )

    # Resolve school
    school_id = None
    if req.school_code:
        s_stmt = select(School).where(School.code == req.school_code.strip())
        school = (await db.execute(s_stmt)).scalar_one_or_none()
        if school:
            school_id = school.id
    if not school_id:
        # Fallback to demo or first active school
        default_s_stmt = select(School).where(School.is_active.is_(True)).limit(1)
        default_s = (await db.execute(default_s_stmt)).scalar_one_or_none()
        if default_s:
            school_id = default_s.id

    # Create UserAccount
    new_user = UserAccount(
        school_id=school_id,
        role=req_role,
        username=req.username.strip(),
        name=req.name.strip() if req.name else req.username.strip(),
        email=req.email.strip() if req.email else None,
        phone=req.phone.strip() if req.phone else None,
        password_hash=get_password_hash(req.password),
        preferred_lang=req.preferred_lang or "en",
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    await db.flush()

    # If student, create StudentProfile
    if req_role == "student":
        student_profile = StudentProfile(
            user_id=new_user.id,
            school_id=school_id,
            grade=req.grade if req.grade else 9,
            section=req.section.upper() if req.section else "A",
            roll_no=None,
            total_xp=0,
            current_streak=0,
            longest_streak=0,
            last_active_at=datetime.now(timezone.utc),
        )
        db.add(student_profile)

    # If parent with linked student username, link them
    if req_role == "parent" and req.linked_student_username:
        st_user_stmt = select(UserAccount).where(
            UserAccount.username == req.linked_student_username.strip(),
            UserAccount.role == "student",
        )
        st_user = (await db.execute(st_user_stmt)).scalar_one_or_none()
        if st_user:
            st_prof_stmt = select(StudentProfile).where(StudentProfile.user_id == st_user.id)
            st_prof = (await db.execute(st_prof_stmt)).scalar_one_or_none()
            if st_prof:
                parent_link = ParentChildLink(
                    parent_user_id=new_user.id,
                    student_id=st_prof.id,
                    relation_type="parent",
                    consent_given=True,
                    consent_at=datetime.now(timezone.utc),
                )
                db.add(parent_link)

    # Generate tokens
    token_payload = {
        "sub": new_user.id,
        "role": new_user.role,
        "school_id": new_user.school_id,
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    auth_token = AuthToken(
        user_id=new_user.id,
        token=refresh_token,
        token_type="refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        is_revoked=False,
    )
    db.add(auth_token)
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserSummary(
            id=new_user.id,
            username=new_user.username,
            role=new_user.role,
            preferred_lang=new_user.preferred_lang,
            name=new_user.name,
            email=new_user.email,
            school_id=new_user.school_id,
        ),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    val = req.username_or_email.strip()
    stmt = select(UserAccount).where(
        or_(UserAccount.username == val, UserAccount.email == val)
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this username or email",
        )
    return MessageResponse(message=f"Verified account for '{user.username}'. Please provide your new password.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserAccount).where(UserAccount.username == req.username.strip())
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )
    user.password_hash = get_password_hash(req.new_password)
    await db.commit()
    return MessageResponse(message="Password reset successfully. You can now sign in.")

