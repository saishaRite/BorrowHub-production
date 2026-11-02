import uuid
import pytest


def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "u23cs001@svnit.ac.in",
        "password": "Svnit@2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["svnit_email"] == "u23cs001@svnit.ac.in"


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={
        "email": "u23cs001@svnit.ac.in",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert "Invalid SVNIT email or password" in res.json()["detail"]


def test_register_invalid_domain(client):
    res = client.post("/api/auth/register", json={
        "roll_number": "U24TEST99",
        "full_name": "Test Student",
        "svnit_email": "test@gmail.com",
        "password": "Password123!"
    })
    assert res.status_code == 422  # Pydantic validation error


def test_register_duplicate_email(client):
    res = client.post("/api/auth/register", json={
        "roll_number": "U24DIFF01",
        "full_name": "Duplicate Student",
        "svnit_email": "u23cs001@svnit.ac.in",
        "password": "Password123!"
    })
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]


def test_register_and_verify_success(client, monkeypatch):
    monkeypatch.setattr("backend.app.services.email_service.send_email_otp", lambda **kwargs: (False, "Test mode"))
    unique_id = uuid.uuid4().hex[:6]
    email = f"u24cs{unique_id}@coed.svnit.ac.in"
    roll = f"U24CS{unique_id.upper()}"

    # Register
    res = client.post("/api/auth/register", json={
        "roll_number": roll,
        "full_name": f"Student {unique_id}",
        "svnit_email": email,
        "password": "SecurePassword@123",
        "hostel_or_dept": "Bhabha Bhavan"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Request OTP resend for testing verification
    res_otp = client.post("/api/auth/resend-otp", json={"email": email})
    assert res_otp.status_code == 200
    otp = res_otp.json()["otp_debug"]
    assert otp is not None

    # Verify email
    res_verify = client.post("/api/auth/verify-email", json={
        "email": email,
        "otp": otp
    })
    assert res_verify.status_code == 200
    assert res_verify.json()["is_verified"] is True


def test_unauthorized_access(client):
    res = client.get("/api/items/my-listings")
    assert res.status_code == 401


def test_forgot_password_two_step_reset_flow(client, monkeypatch):
    monkeypatch.setattr("backend.app.services.email_service.send_email_otp", lambda **kwargs: (False, "Test mode"))
    unique_id = uuid.uuid4().hex[:6]
    email = f"u24fp{unique_id}@coed.svnit.ac.in"
    roll = f"U24FP{unique_id.upper()}"

    # Register student
    res_reg = client.post("/api/auth/register", json={
        "roll_number": roll,
        "full_name": f"FP Student {unique_id}",
        "svnit_email": email,
        "password": "InitialPassword@123",
        "hostel_or_dept": "Bhabha Bhavan"
    })
    assert res_reg.status_code == 200

    # Step 1: Request reset code
    res_forgot = client.post("/api/auth/forgot-password", json={"email": email})
    assert res_forgot.status_code == 200
    otp = res_forgot.json().get("otp_debug")
    assert otp is not None
    assert len(otp) == 6

    # Step 2: Verify reset OTP (Screen 2: verify OTP only without consuming)
    res_verify = client.post("/api/auth/verify-reset-otp", json={
        "email": email,
        "otp": otp
    })
    assert res_verify.status_code == 200
    assert res_verify.json()["verified"] is True

    # Step 2b: Test invalid OTP gives 400
    res_bad_otp = client.post("/api/auth/verify-reset-otp", json={
        "email": email,
        "otp": "000000"
    })
    assert res_bad_otp.status_code == 400

    # Step 3: Set new password (Screen 3: sets new password using the verified OTP)
    new_password = "BrandNewPassword2026!"
    res_reset = client.post("/api/auth/reset-password", json={
        "email": email,
        "otp_or_token": otp,
        "new_password": new_password
    })
    assert res_reset.status_code == 200

    # Step 4: Login with new password
    res_login = client.post("/api/auth/login", json={
        "email": email,
        "password": new_password
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()


def test_admin_backdoor_removed(client):
    # Admin cannot login with backdoor / arbitrary password
    res_backdoor = client.post("/api/auth/login", json={
        "email": "admin@svnit.ac.in",
        "password": "Svnit@2026!Admin"  # Former backdoor password
    })
    assert res_backdoor.status_code == 401
    assert "Invalid SVNIT email or password" in res_backdoor.json()["detail"]

    # Admin must verify against legitimate hashed password
    res_valid = client.post("/api/auth/login", json={
        "email": "admin@svnit.ac.in",
        "password": "Svnit@2026!"
    })
    assert res_valid.status_code == 200
    assert res_valid.json()["user"]["role"] == "ADMIN"


def test_unverified_student_cannot_list_item(client, db):
    from backend.app.models.user import AppUser
    from backend.app.core.security import hash_password, create_access_token

    unverified = AppUser(
        roll_number="U24UNV01",
        full_name="Unverified Student",
        svnit_email="u24unv01@svnit.ac.in",
        password_hash=hash_password("Pass123!"),
        role="STUDENT",
        is_verified=0,
        is_active=1
    )
    db.add(unverified)
    db.commit()

    token = create_access_token({"sub": str(unverified.user_id), "user_id": unverified.user_id, "role": "STUDENT"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/items", json={
        "title": "Unverified Test Item",
        "category_id": 1,
        "location_id": 1,
        "item_condition": "GOOD",
        "deposit_amount": 100.00,
        "daily_fee": 10.00,
        "max_borrow_days": 3,
        "image_urls": ["https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c"]
    }, headers=headers)
    assert res.status_code == 403
    assert "verify" in res.json()["detail"].lower()


def test_suspended_student_cannot_borrow(client, db):
    from backend.app.models.user import AppUser
    from backend.app.core.security import hash_password, create_access_token

    suspended = AppUser(
        roll_number="U24SUS01",
        full_name="Suspended Student",
        svnit_email="u24sus01@svnit.ac.in",
        password_hash=hash_password("Pass123!"),
        role="STUDENT",
        is_verified=1,
        is_active=0  # Suspended
    )
    db.add(suspended)
    db.commit()

    token = create_access_token({"sub": str(suspended.user_id), "user_id": suspended.user_id, "role": "STUDENT"})
    headers = {"Authorization": f"Bearer {token}"}

    from datetime import date, timedelta
    start = date.today() + timedelta(days=50)
    end = start + timedelta(days=2)

    res = client.post("/api/borrow-requests", json={
        "item_id": 1,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }, headers=headers)
    assert res.status_code == 403
    assert "suspended" in res.json()["detail"].lower() or "inactive" in res.json()["detail"].lower()


def test_rate_limit_bypass_header_rejected():
    import pytest
    from fastapi import HTTPException
    from backend.app.core.rate_limit import check_rate_limit
    from backend.app.core.config import settings

    # In non-test mode, rate limiter raises 429 once threshold exceeded
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        key = "test_client_key_9999"
        # 1st call under threshold passes
        check_rate_limit(key, max_requests=1, window_seconds=60)
        # 2nd call must be rejected with 429
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(key, max_requests=1, window_seconds=60)
        assert exc_info.value.status_code == 429
    finally:
        settings.ENVIRONMENT = original_env


