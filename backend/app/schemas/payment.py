from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict





class CashPaymentConfirmRequest(BaseModel):
    payment_id: int


class PaymentOut(BaseModel):
    payment_id: int
    loan_id: int
    payer_id: int
    payer_name: Optional[str] = None
    payee_id: int
    payee_name: Optional[str] = None
    payment_type: str
    method: str
    payment_status: str
    amount: Decimal
    transaction_reference: Optional[str] = None
    gateway_order_id: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
