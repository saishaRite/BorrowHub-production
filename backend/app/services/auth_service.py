from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.security import hash_password, verify_password, create_access_token, generate_otp, hash_token_or_otp
from backend.app.models.user import AppUser, AuthToken
from backend.app.schemas.auth import UserRegister, UserLogin, UserProfile


def register_user(db: Session, data: UserRegister) -> Tuple[AppUser, str]:
    """Register a new student account and create an email verification OTP."""
    # Check duplicate roll number
    if db.query(AppUser).filter(AppUser.roll_number == data.roll_number.strip().upper()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roll number '{data.roll_number}' is already registered."
        )

    # Check duplicate email
    email = data.svnit_email.strip().lower()
    if db.query(AppUser).filter(AppUser.svnit_email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' is already registered. Please sign in."
        )

    # Create user
    pw_hash = hash_password(data.password)
    admin_list = [e.lower() for e in getattr(settings, "ADMIN_EMAILS", [])]
    assigned_role = "ADMIN" if email in admin_list else "STUDENT"
    user = AppUser(
        roll_number=data.roll_number.strip().upper(),
        full_name=data.full_name.strip(),
        svnit_email=email,
        phone=data.phone.strip() if data.phone else None,
        hostel_or_dept=data.hostel_or_dept.strip() if data.hostel_or_dept else None,
        password_hash=pw_hash,
        role=assigned_role,
        is_verified=0,
        is_active=1
    )
    db.add(user)
    db.flush()

    # Generate 6-digit email verification OTP
    otp = generate_otp(6)
    token_hash = hash_token_or_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    auth_token = AuthToken(
        user_id=user.user_id,
        token_type="EMAIL_OTP",
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(auth_token)
    db.commit()
    db.refresh(user)

    return user, otp


def verify_email_otp(db: Session, email: str, otp: str) -> AppUser:
    """Verify email OTP and mark student account verified."""
    email = email.strip().lower()
    user = db.query(AppUser).filter(AppUser.svnit_email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )
    if user.is_verified:
        return user

    token_hash = hash_token_or_otp(otp.strip())
    now = datetime.now(timezone.utc)

    token = db.query(AuthToken).filter(
        AuthToken.user_id == user.user_id,
        AuthToken.token_type == "EMAIL_OTP",
        AuthToken.token_hash == token_hash,
        AuthToken.expires_at > now,
        AuthToken.used_at.is_(None)
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification OTP."
        )

    token.used_at = now
    user.is_verified = 1
    db.commit()
    db.refresh(user)
    return user


def resend_verification_otp(db: Session, email: str) -> str:
    """Generate and return a new email OTP for an unverified account."""
    email = email.strip().lower()
    user = db.query(AppUser).filter(AppUser.svnit_email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already verified."
        )

    otp = generate_otp(6)
    token_hash = hash_token_or_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    auth_token = AuthToken(
        user_id=user.user_id,
        token_type="EMAIL_OTP",
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(auth_token)
    db.commit()
    return otp


def authenticate_user(db: Session, login_data: UserLogin) -> Tuple[AppUser, str]:
    """Authenticate student with email and password and issue JWT."""
    email = login_data.email.strip().lower()
    user = db.query(AppUser).filter(
        AppUser.svnit_email == email,
        AppUser.deleted_at.is_(None)
    ).first()

    valid_password = verify_password(login_data.password, user.password_hash) if user else False

    if not user or not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SVNIT email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is suspended. Contact campus admin."
        )

    # Ensure configured admin emails have ADMIN role
    admin_list = [e.lower() for e in getattr(settings, "ADMIN_EMAILS", [])]
    if email in admin_list and user.role != "ADMIN":
        user.role = "ADMIN"
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role, "email": user.svnit_email}
    )
    return user, access_token


def request_password_reset(db: Session, email: str) -> str:
    """Create a password reset OTP for the user."""
    email = email.strip().lower()
    user = db.query(AppUser).filter(
        AppUser.svnit_email == email,
        AppUser.deleted_at.is_(None)
    ).first()
    if not user:
        # Don't leak whether email exists
        return "123456"

    otp = generate_otp(6)
    token_hash = hash_token_or_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    token = AuthToken(
        user_id=user.user_id,
        token_type="PASSWORD_RESET",
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(token)
    db.commit()
    return otp


def verify_password_reset_otp(db: Session, email: str, otp_or_token: str) -> bool:
    """Verify that a password reset OTP is valid and not expired, without consuming it yet."""
    email = email.strip().lower()
    user = db.query(AppUser).filter(
        AppUser.svnit_email == email,
        AppUser.deleted_at.is_(None)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    token_hash = hash_token_or_otp(otp_or_token.strip())
    now = datetime.now(timezone.utc)

    token = db.query(AuthToken).filter(
        AuthToken.user_id == user.user_id,
        AuthToken.token_type == "PASSWORD_RESET",
        AuthToken.token_hash == token_hash,
        AuthToken.expires_at > now,
        AuthToken.used_at.is_(None)
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code. Please check your email or request a new code."
        )
    return True


def reset_password(db: Session, email: str, otp_or_token: str, new_password: str) -> bool:
    """Reset user password using verification token/OTP."""
    email = email.strip().lower()
    user = db.query(AppUser).filter(
        AppUser.svnit_email == email,
        AppUser.deleted_at.is_(None)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    token_hash = hash_token_or_otp(otp_or_token.strip())
    now = datetime.now(timezone.utc)

    token = db.query(AuthToken).filter(
        AuthToken.user_id == user.user_id,
        AuthToken.token_type == "PASSWORD_RESET",
        AuthToken.token_hash == token_hash,
        AuthToken.expires_at > now,
        AuthToken.used_at.is_(None)
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code."
        )

    token.used_at = now
    user.password_hash = hash_password(new_password)
    db.commit()
    return True
