# BorrowHub — Complete Full-Stack Campus Resource Sharing Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0.16+-4479A1.svg?logo=mysql)](https://mysql.com)
[![Tests](https://img.shields.io/badge/Pytest-13%20Passed-success.svg)](backend/tests/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Share · Borrow · Grow**  
> A student-to-student resource-sharing marketplace designed specifically for **SVNIT Surat**.

---

## 1. Overview & Campus Context

Students on campus frequently need expensive tools, scientific equipment, academic books, sports gear, and electronics for brief periods—such as a Casio fx-991EX calculator during exam week, a mini-drafter for engineering drawing, lab coats for chemistry practicals, or a multimeter for electrical lab sessions. Purchasing these items brand new is costly and wasteful.

**BorrowHub** solves this with an authentic, student-to-student sharing economy platform tailored to the SVNIT community:
- **Verified Student Identity:** Restricted to official `@svnit.ac.in` and `@coed.svnit.ac.in` email addresses with OTP verification.
- **Fair, Independent Pricing:** Daily rental fees + refundable security deposit custody.
- **Physical Two-Party Handshake:** Cryptographic 6-digit OTP codes for verified pickup and return inspections.
- **Double-Booking Immunity:** Concurrency-protected calendar reservations enforced at the database level.
- **Reputation & Trust:** Peer reviews (1–5 stars) and automated trust score auditing.

---

## 2. Technology Stack

### Frontend
* **Core:** HTML5, CSS3, Vanilla JavaScript (ES2022)
* **Design Identity:** Custom SVNIT campus palette (Sage green `#3f7664`, Cream `#f8f6ef`, Terracotta coral `#f26355`, Forest ink `#183e34`)
* **Communication:** Fetch API with automatic JWT Bearer injection
* **Features:** Live date calculation, image upload preview gallery, responsive mobile navigation, modal dialogs

### Backend
* **Framework:** FastAPI (Python 3.10+)
* **ORM:** SQLAlchemy 2.x
* **Data Validation:** Pydantic V2
* **Migrations:** Alembic
* **Authentication:** Stateless JWT tokens (`PyJWT`) with Bcrypt password hashing
* **Rate Limiting:** Sliding-window rate limiter on authentication routes

### Database
* **Engine:** MySQL 8.0.16+ InnoDB
* **Integrity:** 23 Native Triggers and Stored Procedures enforcing date availability, non-self borrowing, inspection checks, and deposit settlement
* **Constraints:** Foreign keys with referential actions, check constraints on email domains and trust scores, composite unique index on `(item_id, booked_date)`

### External Integrations
* **Payments:** Razorpay Standard Checkout (Test Mode + Webhook verification)
* **Image Hosting:** Cloudinary CDN integration with local fallback support

---

## 3. High-Level Architecture & Lifecycle

```
[Student A (Owner)]                   [Student B (Borrower)]
       │                                       │
       │ 1. List Item (Casio fx-991EX)         │
       ├──────────────────────────────────────>│ (Marketplace)
       │                                       │
       │                                       │ 2. Select Dates & Submit Request
       │<──────────────────────────────────────┤    (Daily Fee: ₹10/day, Deposit: ₹200)
       │                                       │
       │ 3. Review & Approve Request           │
       ├──────────────────────────────────────>│ (Dates Reserved in BOOKED_DATE)
       │                                       │
       │                                       │ 4. Complete Payment (Rental + Deposit)
       │                                       │    (Status -> SCHEDULED)
       │                                       │    (Borrower receives Handover OTP: 729401)
       │                                       │
       │ 5. Physical Handover at Campus Spot   │
       │    Owner verifies Borrower's OTP      │
       │<──────────────────────────────────────┤
       │ (Status -> ACTIVE)                    │
       │                                       │
       │                                       │ 6. Use Item & Meet for Return
       │                                       │    (Borrower shares Return OTP: 834192)
       │ 7. Inspect Item & Verify Return OTP   │
       │    Deposit Settled (Full Refund)      │
       │<──────────────────────────────────────┤
       │ (Status -> RETURNED)                  │
       │                                       │
       │ 8. Mutual Peer Reviews (5 Stars ★)    │
       │<═════════════════════════════════════>│
```

---

## 4. Quickstart Guide

> **Note on Directory Location:** Always execute commands and scripts from the **project root folder** (do not `cd backend`). All modules, batch files, and configuration are structured for root execution.

### 1. Database Setup
```bash
# Connect to MySQL and apply the master schema & triggers
mysql -u root -p < database/schema.sql

# Load the campus seed data (users, categories, locations, sample items)
mysql -u root -p borrowhub < database/seed.sql
```

### 2. Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run Application Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Frontend Application:** `http://localhost:8000`
* **Swagger API Docs:** `http://localhost:8000/api/docs`
* **ReDoc Specifications:** `http://localhost:8000/api/redoc`

---

## 5. Pre-Configured Student Test Accounts

All pre-configured accounts use the default password: **`Svnit@2026!`**

| Name | Role | Email | Roll Number | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Priya Sharma** | `STUDENT` | `priya@coed.svnit.ac.in` | `U22CS001` | Item owner with active listings (Calculator, Drafter) |
| **Aarav Patel** | `STUDENT` | `aarav@coed.svnit.ac.in` | `U22CS014` | Borrower account ready to request items |
| **Rohit Verma** | `STUDENT` | `rohit@coed.svnit.ac.in` | `U22EE028` | Electrical student peer |
| **Admin User** | `ADMIN` | `admin@svnit.ac.in` | `SVNIT-ADMIN-01` | Platform moderation, audit logs & dispute resolution |

> **Pro-Tip:** In the web interface, click on the **Demo Quick Sign-In** chips (Priya, Aarav, Rohit, Admin) to authenticate instantly with 1 click!

---

## 6. Automated Test Suite

BorrowHub includes a comprehensive pytest test suite verifying all critical business flows:

```bash
python -m pytest backend/tests -v
```

### Test Coverage Highlights:
- ✅ `test_admin_endpoints_access_control`: Role-based access control (403 for non-admins).
- ✅ `test_admin_user_moderation`: Admin account suspension and status management.
- ✅ `test_login_success` & `test_login_wrong_password`: Valid credentials and rejection.
- ✅ `test_register_invalid_domain`: Rejection of non-SVNIT emails.
- ✅ `test_register_duplicate_email`: Prevention of duplicate account creation.
- ✅ `test_register_and_verify_success`: OTP verification and activation flow.
- ✅ `test_unauthorized_access`: Protection of private endpoints.
- ✅ `test_self_borrowing_prevention`: Rejection of requests by owners on their own items.
- ✅ `test_complete_borrow_loan_and_return_lifecycle`: Full end-to-end borrowing, approval, payment, handover OTP handshake, return OTP handshake, deposit settlement, and review creation.
- ✅ `test_list_categories_and_locations`: Database-backed categories and pickup spots.
- ✅ `test_create_and_manage_item`: Item CRUD, search query, and category filters.
- ✅ `test_payment_flow`: Razorpay order creation, signature verification, and cash fallback.

---

## 7. Project Documentation Index

Detailed documentation files are available in the [`docs/`](docs/) directory:
* [API Documentation (`docs/API_DOCUMENTATION.md`)](docs/API_DOCUMENTATION.md): Complete REST endpoint guide with request and response payloads.
* [Database Architecture (`docs/DATABASE_DESIGN.md`)](docs/DATABASE_DESIGN.md): Schema design, ER diagram, 23 triggers and stored procedures.
* [Security Assessment (`docs/SECURITY_ASSESSMENT.md`)](docs/SECURITY_ASSESSMENT.md): Zero-trust security model, OTP cryptographic hashing, and threat mitigation.
* [Payment & Cloudinary Guide (`docs/PAYMENT_AND_CLOUDINARY_GUIDE.md`)](docs/PAYMENT_AND_CLOUDINARY_GUIDE.md): Razorpay test/live setup and Cloudinary media upload.
* [Deployment Guide (`docs/DEPLOYMENT.md`)](docs/DEPLOYMENT.md): Local development and production deployment (Docker, Nginx, Railway/Render).
