from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.models.user import AppUser
from backend.app.schemas.payment import CashPaymentConfirmRequest, PaymentOut
from backend.app.services.payment_service import confirm_cash_payment, get_payment_history

router = APIRouter(prefix="/payments", tags=["Cash Payments & Settlement"])


@router.post("/cash-confirm", response_model=PaymentOut)
def confirm_cash(
    data: CashPaymentConfirmRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm receipt of physical cash payment (lender/payee or administrator only)."""
    return confirm_cash_payment(db, data.payment_id, current_user)


@router.get("/history", response_model=List[PaymentOut])
def payment_history(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve personal cash payment records and deposit settlement history."""
    return get_payment_history(db, current_user)
