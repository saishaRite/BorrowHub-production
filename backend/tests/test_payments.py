import random
from datetime import date, timedelta
from backend.app.models.payment import Payment


def test_cash_payment_flow_and_authorization(
    client, auth_headers_student_a, auth_headers_student_b, db
):
    # Student A creates a dedicated item
    item_res = client.post("/api/items", json={
        "title": f"Cash Payment Breadboard {random.randint(1000, 9999)}",
        "category_id": 2,
        "location_id": 1,
        "description": "Electronics breadboard for circuit prototyping.",
        "item_condition": "NEW",
        "deposit_amount": 150.00,
        "daily_fee": 10.00,
        "max_borrow_days": 7,
        "image_urls": ["https://images.unsplash.com/photo-1518770660439-4636190af475"]
    }, headers=auth_headers_student_a)
    assert item_res.status_code == 201
    item_id = item_res.json()["item_id"]

    today = date.today()
    offset = random.randint(20, 300)
    start = today + timedelta(days=offset)
    end = today + timedelta(days=offset + 2)

    # Student B requests Item
    req_res = client.post("/api/borrow-requests", json={
        "item_id": item_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "request_message": "Need for microprocessors project"
    }, headers=auth_headers_student_b)
    assert req_res.status_code == 201
    req_id = req_res.json()["request_id"]

    # Student A approves
    app_res = client.post(f"/api/borrow-requests/{req_id}/approve", headers=auth_headers_student_a)
    assert app_res.status_code == 200
    loan_id = app_res.json()["loan_id"]

    # Create a pending cash payment record for the loan
    cash_payment = Payment(
        loan_id=loan_id,
        payer_id=req_res.json()["borrower_id"],
        payee_id=item_res.json()["owner_id"],
        payment_type="RENTAL_FEE",
        method="CASH",
        payment_status="PENDING",
        amount=30.00,
        transaction_reference=f"CASH_TEST_{loan_id}_{random.randint(1000, 9999)}"
    )
    db.add(cash_payment)
    db.commit()
    db.refresh(cash_payment)
    payment_id = cash_payment.payment_id

    # 1. Self-confirmation exploit: Borrower (Student B) attempts to confirm their own cash payment -> 403 Forbidden!
    self_confirm_res = client.post("/api/payments/cash-confirm", json={
        "payment_id": payment_id
    }, headers=auth_headers_student_b)
    assert self_confirm_res.status_code == 403
    assert "recipient" in self_confirm_res.json()["detail"].lower()

    # 2. Legitimate confirmation: Payee (Student A, lender) confirms cash receipt -> 200 OK
    payee_confirm_res = client.post("/api/payments/cash-confirm", json={
        "payment_id": payment_id
    }, headers=auth_headers_student_a)
    assert payee_confirm_res.status_code == 200
    confirmed_data = payee_confirm_res.json()
    assert confirmed_data["payment_status"] == "COMPLETED"
    assert confirmed_data["method"] == "CASH"

    # 3. Duplicate confirmation idempotency: Confirming again returns completed record safely
    dup_res = client.post("/api/payments/cash-confirm", json={
        "payment_id": payment_id
    }, headers=auth_headers_student_a)
    assert dup_res.status_code == 200
    assert dup_res.json()["payment_status"] == "COMPLETED"

    # 4. Payment history inspection
    history_res = client.get("/api/payments/history", headers=auth_headers_student_b)
    assert history_res.status_code == 200
    history = history_res.json()
    assert any(p["payment_id"] == payment_id for p in history)
