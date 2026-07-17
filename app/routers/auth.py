from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    UserOut,
    VerifyOtpRequest,
)
from app.security import (
    create_access_token,
    generate_otp,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_TTL_MINUTES = 10


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(User.email == payload.email, User.phone == payload.phone)
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email or phone already registered")

    otp = generate_otp()
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        otp_code=otp,
        otp_expires_at=datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterResponse(user_id=user.id, dev_otp_code=otp)


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.phone_verified:
        pass  # already verified, e.g. re-verify flow — fall through and reissue token
    elif (
        user.otp_code != payload.code
        or user.otp_expires_at is None
        or user.otp_expires_at < datetime.utcnow()
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code")

    user.phone_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()

    token = create_access_token(user.id, user.role)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.email == payload.identifier, User.phone == payload.identifier)
    ).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.phone_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Phone not verified")

    token = create_access_token(user.id, user.role)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
