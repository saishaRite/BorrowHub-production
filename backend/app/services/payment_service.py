import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.models.borrow import Loan, BorrowRequest
from backend.app.models.catalog import Item
from backend.app.models.payment import Payment
from backend.app.models.user import AppUser
from backend.app.services.notification_service import create_notification
from backend.app.schemas.payment import PaymentOut


def confirm_cash_payment(db: Session, payment_id: int, payee: AppUser) -> PaymentOut:
    payment = db.query(Payment).options(joinedload(Payment.loan)).filter(
        Payment.payment_id == payment_id
    ).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    if payment.payee_id != payee.user_id and payee.role not in ("ADMIN", "MODERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payment recipient (lender) or an authorized administrator can confirm cash receipt."
        )

    if payment.payment_status == "COMPLETED":
        return PaymentOut.model_validate(payment)

    payment.method = "CASH"
    payment.confirmed_by_user_id = payee.user_id
    if not payment.transaction_reference:
        payment.transaction_reference = f"CASH_CONFIRM_{payment.payment_id}_{uuid.uuid4().hex[:6]}"
    payment.payment_status = "COMPLETED"
    payment.paid_at = datetime.now(timezone.utc)

    if payment.loan and payment.loan.agreed_deposit > 0 and payment.payment_type == "DEPOSIT":
        payment.loan.deposit_status = "HELD"

    db.commit()
    db.refresh(payment)
    return PaymentOut.model_validate(payment)


def get_payment_history(db: Session, user: AppUser) -> List[PaymentOut]:
    payments = db.query(Payment).options(
        joinedload(Payment.payer),
        joinedload(Payment.payee)
    ).filter(
        (Payment.payer_id == user.user_id) | (Payment.payee_id == user.user_id)
    ).order_by(Payment.created_at.desc()).all()

    results = []
    for p in payments:
        results.append(PaymentOut(
            payment_id=p.payment_id,
            loan_id=p.loan_id,
            payer_id=p.payer_id,
            payer_name=p.payer.full_name if p.payer else "Student",
            payee_id=p.payee_id,
            payee_name=p.payee.full_name if p.payee else "Owner",
            payment_type=p.payment_type,
            method=p.method,
            payment_status=p.payment_status,
            amount=p.amount,
            transaction_reference=p.transaction_reference,
            gateway_order_id=p.gateway_order_id,
            created_at=p.created_at,
            paid_at=p.paid_at,
        ))
    return results
