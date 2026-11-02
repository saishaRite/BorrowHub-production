"""BorrowHub email delivery via Brevo HTTPS API, with optional local SMTP fallback."""

from __future__ import annotations

import html
import logging
import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from backend.app.core.config import settings

logger = logging.getLogger("borrowhub.email")
BREVO_SEND_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"
PRODUCTION_ENVIRONMENTS = {"production", "prod", "staging"}


def _is_production() -> bool:
    return str(settings.ENVIRONMENT).strip().lower() in PRODUCTION_ENVIRONMENTS


def _sender() -> Dict[str, str]:
    """Return the verified sender configured for Brevo."""
    sender_email = str(getattr(settings, "BREVO_SENDER_EMAIL", "") or "").strip()
    sender_name = str(getattr(settings, "SMTP_FROM_NAME", "BorrowHub SVNIT") or "BorrowHub SVNIT").strip()
    if not sender_email:
        raise ValueError("BREVO_SENDER_EMAIL is not configured")
    return {"name": sender_name, "email": sender_email}


def _send_via_brevo(
    to_email: str,
    recipient_name: str,
    subject: str,
    text_content: str,
    html_content: str,
) -> Tuple[bool, str]:
    api_key = str(getattr(settings, "BREVO_API_KEY", "") or "").strip()
    if not api_key:
        return False, "Brevo API key is not configured."

    try:
        sender = _sender()
    except ValueError as exc:
        logger.error("Brevo sender configuration error: %s", exc)
        return False, "Brevo sender email is not configured."

    payload: Dict[str, Any] = {
        "sender": sender,
        "to": [{"email": to_email, "name": recipient_name or "Student"}],
        "subject": subject,
        "textContent": text_content,
        "htmlContent": html_content,
    }
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    try:
        response = httpx.post(
            BREVO_SEND_EMAIL_URL,
            headers=headers,
            json=payload,
            timeout=httpx.Timeout(20.0),
        )
        response.raise_for_status()
        logger.info("Brevo accepted an email for delivery to %s", to_email)
        return True, f"Email accepted for delivery to {to_email}."
    except httpx.HTTPStatusError as exc:
        # Do not log request headers or the API key.
        response_text = (exc.response.text or "")[:500]
        logger.error(
            "Brevo rejected email to %s (HTTP %s): %s",
            to_email,
            exc.response.status_code,
            response_text,
        )
        return False, "Brevo rejected the email request. Check sender verification and API permissions."
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        logger.error("Brevo network error while sending to %s: %s", to_email, type(exc).__name__)
        return False, "Could not connect to the Brevo email service."
    except ValueError as exc:
        logger.error("Brevo sender configuration error: %s", exc)
        return False, "Brevo sender email is not configured."


def _send_via_smtp(
    to_email: str,
    subject: str,
    text_content: str,
    html_content: str,
) -> Tuple[bool, str]:
    """Optional SMTP fallback for local development; Render should use Brevo HTTPS."""
    smtp_user = str(getattr(settings, "SMTP_USER", "") or "").strip()
    smtp_password = str(getattr(settings, "SMTP_PASSWORD", "") or "").strip()
    if not smtp_user or not smtp_password:
        return False, "SMTP credentials are not configured."

    smtp_host = str(settings.SMTP_HOST).strip()
    smtp_port = int(settings.SMTP_PORT)
    from_name = str(settings.SMTP_FROM_NAME or "BorrowHub SVNIT").strip()
    from_email = str(getattr(settings, "SMTP_FROM_EMAIL", "") or smtp_user).strip() or smtp_user

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message.attach(MIMEText(text_content, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], message.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.ehlo()
                if bool(settings.SMTP_TLS):
                    server.starttls()
                    server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], message.as_string())
        logger.info("SMTP accepted an email for delivery to %s", to_email)
        return True, f"Email accepted for delivery to {to_email}."
    except Exception as exc:  # SMTP is optional and must not crash an API request.
        logger.error("SMTP delivery failed for %s: %s", to_email, type(exc).__name__)
        return False, "SMTP email delivery failed."


def _deliver_email(
    to_email: str,
    recipient_name: str,
    subject: str,
    text_content: str,
    html_content: str,
) -> Tuple[bool, str]:
    """Prefer Brevo HTTPS API; use SMTP only when Brevo is not configured."""
    if str(getattr(settings, "BREVO_API_KEY", "") or "").strip():
        return _send_via_brevo(to_email, recipient_name, subject, text_content, html_content)
    return _send_via_smtp(to_email, subject, text_content, html_content)


def _write_local_otp_debug(
    to_email: str,
    recipient_name: str,
    otp: str,
    purpose: str,
) -> None:
    """Keep the existing local test workflow; never call this in production."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        static_dir = os.path.join(backend_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        record_path = os.path.join(static_dir, "latest_sent_otp.json")
        with open(record_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "to_email": to_email,
                    "name": recipient_name,
                    "otp": otp,
                    "purpose": purpose,
                },
                file,
            )
    except OSError as exc:
        logger.warning("Could not write local OTP debug record: %s", type(exc).__name__)


def send_email_otp(
    to_email: str,
    recipient_name: str,
    otp: str,
    purpose: str = "VERIFICATION",
) -> Tuple[bool, str]:
    """Send a registration or password-reset OTP by Brevo HTTPS API or local SMTP."""
    clean_email = (to_email or "").strip().lower()
    clean_name = (recipient_name or "Student").strip() or "Student"
    safe_name = html.escape(clean_name)
    safe_otp = html.escape(str(otp))

    if purpose == "PASSWORD_RESET":
        subject = "Your BorrowHub password reset code"
        action_text = "reset your BorrowHub account password"
        intro_text = "Use the code below to reset your BorrowHub account password."
    else:
        subject = "Your BorrowHub verification code"
        action_text = "verify your official SVNIT student account"
        intro_text = "Thank you for joining BorrowHub. Use the code below to verify your official SVNIT student account."

    expiry_minutes = int(settings.OTP_EXPIRY_MINUTES)
    text_content = f"""Hello {clean_name},

Your BorrowHub verification code is: {otp}

Use this 6-digit code to {action_text}.
This code will expire in {expiry_minutes} minutes.

If you did not request this code, please ignore this email.

Best regards,
BorrowHub Team
SVNIT Surat Campus Community
"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;background:#f8f6ef;margin:0;padding:20px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e5e0d3;">
    <div style="background:#8b2b1d;color:#fff;padding:24px 28px;text-align:center;">
      <h1 style="margin:0;font-size:22px;">BorrowHub</h1>
      <p style="margin:4px 0 0;font-size:13px;">SVNIT Surat Campus Resource Sharing Platform</p>
    </div>
    <div style="padding:30px 28px;color:#2d3748;line-height:1.6;font-size:15px;">
      <p>Hello <strong>{safe_name}</strong>,</p>
      <p>{html.escape(intro_text)}</p>
      <div style="background:#fdfaf3;border:2px dashed #8b2b1d;border-radius:12px;padding:18px;text-align:center;margin:24px 0;">
        <div style="font-size:34px;font-weight:800;letter-spacing:8px;color:#8b2b1d;font-family:monospace;">{safe_otp}</div>
        <div style="font-size:12px;color:#718096;margin-top:6px;">Valid for {expiry_minutes} minutes</div>
      </div>
      <p style="font-size:13px;color:#718096;">Security Notice: BorrowHub administrators will never ask for your verification code or password.</p>
    </div>
    <div style="background:#f8f6ef;padding:18px 28px;font-size:12px;color:#718096;text-align:center;border-top:1px solid #e5e0d3;">
      Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat<br>Share &bull; Borrow &bull; Grow
    </div>
  </div>
</body>
</html>"""

    sent, detail = _deliver_email(clean_email, clean_name, subject, text_content, html_content)
    if sent:
        return True, f"Verification email accepted for delivery to {clean_email}."

    if _is_production():
        # Never reveal or persist OTP values when a production email provider fails.
        logger.error("OTP email delivery failed for %s: %s", clean_email, detail)
        return False, "Email delivery is temporarily unavailable. Please try again later."

    logger.warning("Local development email fallback used for %s: %s", clean_email, detail)
    print("=" * 72)
    print("[BORROWHUB EMAIL - LOCAL DEVELOPMENT ONLY]")
    print(f"To: {clean_email} ({clean_name})")
    print(f"Subject: {subject}")
    print(f"OTP: {otp}")
    print(f"Expires in: {expiry_minutes} minutes")
    print("=" * 72)
    _write_local_otp_debug(clean_email, clean_name, str(otp), purpose)
    return False, f"OTP generated for local development. Configure Brevo to deliver real email."


def _safe_http_url(value: str) -> Optional[str]:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return url


def send_dispute_alert_email(
    admin_email: str,
    admin_name: str,
    dispute_id: int,
    loan_id: int,
    dispute_type: str,
    claimed_amount: float,
    description: str,
    raised_by_name: str,
    evidence_urls: List[str],
) -> Tuple[bool, str]:
    """Send a dispute alert to an administrator, including safe evidence links."""
    clean_email = (admin_email or "").strip().lower()
    clean_name = (admin_name or "Campus Administrator").strip() or "Campus Administrator"
    subject = f"[BorrowHub Dispute Alert] New Damage Claim #{dispute_id} (Loan #{loan_id})"

    valid_urls = [url for url in (evidence_urls or []) if _safe_http_url(url)]
    evidence_text = "\n".join(f"- {url}" for url in valid_urls) if valid_urls else "No photo attachments provided."
    evidence_html = "".join(
        '<a href="{0}" target="_blank" rel="noopener noreferrer" style="display:inline-block;margin:4px;">'
        '<img src="{0}" alt="Dispute evidence" style="width:90px;height:90px;object-fit:cover;border-radius:6px;border:1px solid #ccc;"></a>'.format(
            html.escape(url, quote=True)
        )
        for url in valid_urls
    ) or '<p style="color:#718096;font-size:13px;">No photo proof attached.</p>'

    app_url = str(getattr(settings, "PUBLIC_APP_URL", "http://127.0.0.1:8000") or "http://127.0.0.1:8000").rstrip("/")
    safe_app_url = html.escape(app_url, quote=True)
    safe_admin_name = html.escape(clean_name)
    safe_dispute_type = html.escape(str(dispute_type))
    safe_raised_by = html.escape(str(raised_by_name))
    safe_description = html.escape(str(description))

    text_content = f"""BorrowHub Campus Manager Alert

A new damage claim or dispute has been filed and requires administrative mediation:

Dispute ID:      #{dispute_id}
Loan ID:         #{loan_id}
Dispute Type:    {dispute_type}
Filed By:        {raised_by_name}
Claimed Amount:  INR {claimed_amount:.2f}
Description:
{description}

Attached Photo Proof:
{evidence_text}

Open the BorrowHub Admin Dashboard: {app_url}
"""

    html_content = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"></head>
<body style="font-family:Segoe UI,sans-serif;background:#f8f6ef;padding:20px;margin:0;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;border:1px solid #e5e0d3;overflow:hidden;">
    <div style="background:#8b2b1d;color:#fff;padding:20px 24px;">
      <h2 style="margin:0;font-size:20px;">BorrowHub Dispute &amp; Damage Claim</h2>
      <p style="margin:4px 0 0;font-size:13px;">Action required by Campus Administration</p>
    </div>
    <div style="padding:24px;color:#2d3748;font-size:14px;line-height:1.6;">
      <p>Hello <strong>{safe_admin_name}</strong>,</p>
      <p>A student has reported an issue requiring deposit mediation:</p>
      <div style="background:#fef2f2;border-left:4px solid #b91c1c;padding:12px 16px;margin:14px 0;border-radius:4px;">
        <p><strong>Dispute:</strong> #{dispute_id} (Loan #{loan_id})</p>
        <p><strong>Type:</strong> {safe_dispute_type}</p>
        <p><strong>Filed by:</strong> {safe_raised_by}</p>
        <p><strong>Claimed Amount:</strong> <strong>INR {claimed_amount:.2f}</strong></p>
      </div>
      <p><strong>Description of Damage / Issue:</strong></p>
      <blockquote style="background:#f9fafb;border:1px solid #e5e7eb;padding:12px;border-radius:6px;margin:8px 0;">{safe_description}</blockquote>
      <p><strong>Attached Photo Proof:</strong></p>
      <div style="margin:8px 0;">{evidence_html}</div>
      <div style="text-align:center;margin-top:24px;">
        <a href="{safe_app_url}" style="background:#8b2b1d;color:#fff;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600;display:inline-block;">Open Admin Panel</a>
      </div>
    </div>
  </div>
</body></html>"""

    sent, detail = _deliver_email(clean_email, clean_name, subject, text_content, html_content)
    if sent:
        return True, f"Admin email alert accepted for delivery to {clean_email}."

    if _is_production():
        logger.error("Dispute alert delivery failed for admin %s: %s", clean_email, detail)
        return False, "Admin email notification is temporarily unavailable."

    logger.warning("Local dispute alert fallback used for %s: %s", clean_email, detail)
    print("=" * 72)
    print("[BORROWHUB ADMIN DISPUTE ALERT - LOCAL DEVELOPMENT ONLY]")
    print(f"To: {clean_email} ({clean_name})")
    print(f"Subject: {subject}")
    print(f"Dispute ID: #{dispute_id}; Loan ID: #{loan_id}")
    print(f"Claimed amount: INR {claimed_amount:.2f}")
    print(f"Evidence photos: {len(valid_urls)}")
    print("=" * 72)
    return False, f"Dispute alert recorded for admin {clean_email}."
