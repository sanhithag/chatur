from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_current_user, get_db
from app.models.user import AuthToken, School, UserAccount
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserSummary,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
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
