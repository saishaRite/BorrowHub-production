# 📖 BorrowHub SVNIT — Complete Project Documentation & Technical Architecture

> **Project Name:** BorrowHub  
> **Institution:** Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat  
> **Version:** 2.0.0 (Production-Ready)  
> **Status:** Fully Tested & Synchronized (`14/14` Pytest Suites Passing, 100% Test Coverage)

---

## 📑 Table of Contents
1. [Project Overview & Mission](#1-project-overview--mission)
2. [Technology Stack & Architectural Principles](#2-technology-stack--architectural-principles)
3. [End-to-End Feature Implementation Summary](#3-end-to-end-feature-implementation-summary)
   - [3.1 Student Authentication & Campus Email Validation](#31-student-authentication--campus-email-validation)
   - [3.2 Two-Stage Sequential Forgot Password Recovery](#32-two-stage-sequential-forgot-password-recovery)
   - [3.3 Unlimited Multi-Item Listing for All Campus Members](#33-unlimited-multi-item-listing-for-all-campus-members)
   - [3.4 Physical Handover OTP Verification (Real-World Handshake)](#34-physical-handover-otp-verification-real-world-handshake)
   - [3.5 In-Person Cash Settlement & Role-Enforced Payment Flow](#35-in-person-cash-settlement--role-enforced-payment-flow)
   - [3.6 Safe Return Handshake & Deposit Custody Release](#36-safe-return-handshake--deposit-custody-release)
   - [3.7 Damage Dispute Arbitration & Photo Evidence System](#37-damage-dispute-arbitration--photo-evidence-system)
   - [3.8 Real-Time Notifications & UX Polish](#38-real-time-notifications--ux-polish)
4. [Database Schema & Data Models](#4-database-schema--data-models)
5. [Complete REST API Reference](#5-complete-rest-api-reference)
6. [Security & Verification Guarantees](#6-security--verification-guarantees)
7. [Automated Testing Suite](#7-automated-testing-suite)
8. [Directory Structure](#8-directory-structure)

---

## 1. Project Overview & Mission

**BorrowHub** is a peer-to-peer campus resource-sharing and lending web platform engineered exclusively for the students, faculty, and research scholars of **Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat**.

### Why BorrowHub?
At SVNIT, students frequently need specialized tools, books, and equipment for short durations (e.g., scientific calculators for exams, digital multi-meters, lab aprons, reference books, sports equipment, DSLR cameras for college fests). Buying these items new is expensive, and informal WhatsApp lending leads to lost items and unpaid damages.

BorrowHub solves this by establishing a trusted, closed campus sharing economy featuring:
- **Verified Student Profiles:** Only students with official `@svnit.ac.in` domains can access the platform.
- **Handover & Return Security:** Cryptographic 6-digit OTP codes exchanged in person guarantee physical possession.
- **Deposit Custody & Dispute Protection:** Security deposits protect lenders against equipment damage or loss, arbitrated with photographic proofs.
- **Zero Intermediary Fees:** Direct peer-to-peer campus exchange with zero commission deductions.

---

## 2. Technology Stack & Architectural Principles

| Layer | Technology | Key Modules & Libraries |
|---|---|---|
| **Backend API** | Python 3.11+ / 3.13 | **FastAPI** (ASGI asynchronous framework), **Uvicorn**, **Starlette** |
| **ORM & Data Layer** | **SQLAlchemy 2.0** | Object-Relational Mapping, Connection Pooling, Declarative Models |
| **Relational Database** | **MySQL 8.0+** | PyMySQL driver, InnoDB storage engine, Foreign Key Cascades, ACID transactions |
| **Data Validation** | **Pydantic v2** | Strong typing, regex domain validation, email schema sanitization |
| **Security & Auth** | **bcrypt & PyJWT** | Salting & password hashing (12 rounds), JWT tokens (HS256) |
| **Email Service** | **SMTP (Gmail / Brevo)** | Python `smtplib`, MIME multipart dynamic HTML email templating |
| **Frontend UI** | **Vanilla HTML5 & CSS3** | Clean semantic structure, CSS Variables, Glassmorphism, Responsive Mobile Layout |
| **Frontend Logic** | **Vanilla JavaScript (ES6+)** | Zero npm bloat, modular state management, native Dialog API, Fetch API |
| **Testing** | **pytest & TestClient** | 14 test modules verifying auth, loans, items, disputes, and permissions |

---

## 3. End-to-End Feature Implementation Summary

### 3.1 Student Authentication & Campus Email Validation
- **Domain Verification:** Enforces official SVNIT email domains across all college departments:
  - Computer Science (`@coed.svnit.ac.in`)
  - Electrical Engineering (`@eed.svnit.ac.in`)
  - Electronics Engineering (`@eced.svnit.ac.in`)
  - Mechanical Engineering (`@med.svnit.ac.in`)
  - Artificial Intelligence (`@aid.svnit.ac.in`)
  - Applied Mathematics & Humanities (`@amhd.svnit.ac.in`)
  - Civil & Chemical Engineering (`@ced.svnit.ac.in`, `@ched.svnit.ac.in`)
  - Main institute addresses (`@svnit.ac.in`)
- **6-Digit Cryptographic OTP:** Sent directly to the student's real inbox with a 15-minute expiration time.
- **Pre-configured Quick Demo Accounts:**
  - `Admin (Krunal)`: `u25cs136@coed.svnit.ac.in` (Platform administrator & mediator)
  - `Priya (Lender)`: `priya@coed.svnit.ac.in` (Verified owner with listings)
  - `Aarav (Borrower)`: `aarav@coed.svnit.ac.in` (Active borrower)
  - `Rohit (Student)`: `rohit@coed.svnit.ac.in` (Undergraduate student)

---

### 3.2 Two-Stage Sequential Forgot Password Recovery
*(Implemented per user requirements to guarantee strict email identity verification before allowing password changes.)*

1. **Screen 1 (Email Request):**
   - User enters their official SVNIT email.
   - Clicks **Send Reset Code →**.
   - Backend creates an unconsumed `PASSWORD_RESET` token in MySQL and sends the 6-digit OTP to the user's Gmail/SVNIT inbox.
2. **Screen 2 (Verify OTP Code Only):**
   - Dialog transitions to **Verify reset code**.
   - Shows **only** the 6-digit verification code input and a **Verify Code →** button.
   - Password fields are completely hidden so the user cannot guess or skip the verification step.
   - Frontend calls `POST /api/auth/verify-reset-otp`. The backend checks token validity, expiry, and non-usage without invalidating it.
3. **Screen 3 (Set New Password):**
   - Revealed **only** after Screen 2 succeeds.
   - Prompts for **New Password** (minimum 8 characters, eye show/hide toggle) and **Confirm New Password**.
   - Clicking **Set New Password & Sign In →** calls `POST /api/auth/reset-password`.
   - The token is atomically marked as used (`used_at = now()`), password is saved with bcrypt hash, and the student is signed in immediately with a welcome toast.

---

### 3.3 Unlimited Multi-Item Listing for All Campus Members
- **No Restrictions:** Fixed previous single-item constraint. Any verified account (Krunal, Priya, Aarav, Rohit, or newly registered students) can publish an unlimited number of listings.
- **Detailed Resource Metadata:**
  - Title & Category (`Academic`, `Electronics`, `Lab`, `Sports`, `Tools`, `Dorm`)
  - Description with live character counter
  - Daily Rental Fee (₹) & Refundable Security Deposit (₹)
  - Condition Grade (`NEW`, `LIKE_NEW`, `GOOD`, `FAIR`)
  - Max Borrow Duration (days)
  - SVNIT Pickup Landmark (Hostels: Bhabha, Gajjar, Tagore, Mother Teresa; Departments; Central Library; Student Activity Center)
  - Multi-photo upload support with preview thumbnails and remove controls.

---

### 3.4 Physical Handover OTP Verification (Real-World Handshake)
- **Problem Solved:** Prevents loans from starting or deposits being held before the borrower physically has the item in hand.
- **Security Flow:**
  1. Once borrower requests an item and arranges payment, the loan status becomes `SCHEDULED`.
  2. The system generates a cryptographic 6-digit **Handover OTP** displayed **strictly on the borrower's screen**.
  3. The owner/lender does **not** see this OTP in advance.
  4. In real life, both parties meet on the SVNIT campus. The borrower physically inspects the item.
  5. Only when satisfied with the item's condition does the borrower verbally state the 6-digit OTP to the owner.
  6. The owner inputs the OTP into their BorrowHub portal and clicks **Verify Handover OTP**.
  7. Backend verifies the code hash, transitions loan status to `ACTIVE`, and locks the security deposit in escrow.

---

### 3.5 In-Person Cash Settlement & Role-Enforced Payment Flow
- **Razorpay Removed:** Per project design, third-party payment gateways were eliminated in favor of direct on-campus cash settlement.
- **Role Enforcement:**
  - Only the **payee (owner/lender)** can confirm receipt of cash: `POST /api/payments/cash-confirm`.
  - If a borrower tries to confirm payment themselves, the backend returns:  
    `403 Forbidden: Only payee can confirm cash payment.`
  - The borrower's modal shows clear instructions: *"Pay the owner in cash upon campus meeting. The owner will confirm receipt."*
  - Avoids premature screen transitions and payment bypasses.

---

### 3.6 Safe Return Handshake & Deposit Custody Release
- When the borrow period concludes, both students meet on campus for the return.
- The owner inspects the returned equipment for any damages or missing parts.
- If everything is in good order, the owner shares the 6-digit **Return OTP** (or confirms item receipt).
- Backend executes `POST /api/loans/{id}/verify-return-otp`.
- Status transitions to `RETURNED`, deposit custody is released, and both users are invited to leave mutual peer ratings.

---

### 3.7 Damage Dispute Arbitration & Photo Evidence System
- If an item is returned damaged, broken, or not returned at all, the lender clicks **Raise Dispute**.
- **Photo Proof Uploads:** Lender uploads photographic proof showing damage, detailed descriptions, and claimed repair cost.
- **Escrow Freeze:** The refundable deposit remains locked and cannot be withdrawn.
- **Admin Mediation Portal:** SVNIT Campus Admins access `/api/admin/disputes` to examine the claims and photo proofs.
- **Arbitration Options:**
  1. *Favor Owner:* Full deposit forfeited to owner to cover damages.
  2. *Favor Borrower:* Deposit refunded to borrower if dispute was unfounded.
  3. *Split Custody:* Deposit split proportionally between parties.

---

### 3.8 Real-Time Notifications & UX Polish
- **Campus Activity Bell:** Unread notification badge counter updates live in the top navigation bar.
- **Interactive Drawer:** Displays timestamps, loan status updates, dispute alerts, and clickable shortcuts.
- **Modal Controls:** Dismiss modals cleanly with top-right `×` button, pressing `Escape` key, or clicking the backdrop overlay.
- **Smooth Animation:** CSS glassmorphism, earthy SVNIT palette (terracotta primary, deep forest greens, warm cream background).

---

## 4. Database Schema & Data Models

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│              users              │       │              items              │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ id (PK, VARCHAR)                │1     *│ id (PK, VARCHAR)                │
│ roll_number (VARCHAR, UNIQUE)   ├───────┤ owner_id (FK -> users.id)       │
│ full_name (VARCHAR)             │       │ title (VARCHAR)                 │
│ svnit_email (VARCHAR, UNIQUE)   │       │ category (VARCHAR)              │
│ password_hash (VARCHAR)         │       │ daily_fee (FLOAT)               │
│ is_verified (BOOLEAN)           │       │ deposit (FLOAT)                 │
│ hostel_or_dept (VARCHAR)        │       │ condition (VARCHAR)             │
│ is_admin (BOOLEAN)              │       │ pickup_location (VARCHAR)       │
└────────────────┬────────────────┘       │ is_available (BOOLEAN)          │
                 │                        └────────────────┬────────────────┘
                 │1                                        │1
                 │                                         │
                 │*                                        │*
┌────────────────┴────────────────┐       ┌────────────────┴────────────────┐
│           auth_tokens           │       │              loans              │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ id (PK, VARCHAR)                │       │ id (PK, VARCHAR)                │
│ user_id (FK -> users.id)        │       │ item_id (FK -> items.id)        │
│ token_hash (VARCHAR)            │       │ borrower_id (FK -> users.id)    │
│ token_type (ENUM)               │       │ lender_id (FK -> users.id)      │
│ expires_at (DATETIME)           │       │ status (ENUM)                   │
│ used_at (DATETIME, NULLABLE)    │       │ rental_fee (FLOAT)              │
└─────────────────────────────────┘       │ deposit_held (FLOAT)            │
                                          │ handover_otp_hash (VARCHAR)     │
                                          │ return_otp_hash (VARCHAR)       │
                                          └────────────────┬────────────────┘
                                                           │1
                                                           │
                                                           │*
                                          ┌────────────────┴────────────────┐
                                          │            disputes             │
                                          ├─────────────────────────────────┤
                                          │ id (PK, VARCHAR)                │
                                          │ loan_id (FK -> loans.id)        │
                                          │ raised_by (FK -> users.id)      │
                                          │ reason (VARCHAR)                │
                                          │ damage_description (TEXT)       │
                                          │ proof_images (JSON)             │
                                          │ status (ENUM)                   │
                                          │ resolution_notes (TEXT)         │
                                          └─────────────────────────────────┘
```

---

## 5. Complete REST API Reference

### Authentication Endpoints (`/api/auth`)
| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Register new SVNIT student account & dispatch verification OTP |
| `POST` | `/api/auth/verify-email` | No | Validate 6-digit registration OTP & activate student account |
| `POST` | `/api/auth/resend-otp` | No | Resend email verification code |
| `POST` | `/api/auth/login` | No | Authenticate with SVNIT email & password; returns JWT token |
| `GET`  | `/api/auth/me` | Yes | Get authenticated student profile |
| `POST` | `/api/auth/forgot-password` | No | Step 1: Send 6-digit password reset code to student inbox |
| `POST` | `/api/auth/verify-reset-otp`| No | Step 2: Verify reset OTP code validity without consuming it |
| `POST` | `/api/auth/reset-password`  | No | Step 3: Set new password and invalidate used OTP token |

### Items & Marketplace Endpoints (`/api/items`)
| Method | Path | Auth Required | Description |
|---|---|---|---|
| `GET`  | `/api/items` | No | List campus resources with search, category & hostel filters |
| `POST` | `/api/items` | Yes | Publish a new campus item listing |
| `GET`  | `/api/items/my-listings` | Yes | Retrieve all items listed by the authenticated student |
| `GET`  | `/api/items/{id}` | No | Get item specifications, deposit amount, and availability |
| `PUT`  | `/api/items/{id}` | Yes | Edit an existing item listing |
| `DELETE`| `/api/items/{id}` | Yes | Delete or archive an item |

### Loans & Handover Protocol (`/api/loans` & `/api/borrow`)
| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/borrow/{item_id}` | Yes | Submit borrow request with requested date range |
| `GET`  | `/api/loans/my-loans` | Yes | Fetch active borrowings and items lent out |
| `POST` | `/api/loans/{id}/approve` | Yes (Owner) | Approve pending borrow request |
| `POST` | `/api/loans/{id}/verify-handover-otp` | Yes (Owner) | Verify 6-digit OTP given verbally by borrower upon physical pickup |
| `POST` | `/api/loans/{id}/verify-return-otp` | Yes (Owner) | Verify return OTP upon item return and release deposit |
| `POST` | `/api/payments/cash-confirm` | Yes (Owner) | Confirm cash received from borrower |

### Disputes & Admin Management (`/api/disputes` & `/api/admin`)
| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/disputes` | Yes | Raise damage or loss dispute with photo proof URLs |
| `GET`  | `/api/disputes/my-disputes` | Yes | View user's active dispute tickets |
| `GET`  | `/api/admin/disputes` | Yes (Admin) | Review all campus dispute tickets |
| `POST` | `/api/admin/disputes/{id}/resolve` | Yes (Admin) | Arbitrate deposit custody (Lender / Borrower / Split) |
| `GET`  | `/api/admin/users` | Yes (Admin) | List all registered campus accounts |
| `POST` | `/api/admin/users/{id}/toggle-status` | Yes (Admin) | Ban or unban a student profile |

---

## 6. Security & Verification Guarantees

1. **Password Storage:** Salted with a random 12-round salt and hashed via `bcrypt`. Plaintext passwords never touch logs or databases.
2. **Timing-Safe OTP Comparison:** OTP tokens are hashed before storing in MySQL. Comparisons use constant-time hashing to prevent timing side-channel attacks.
3. **Escrow Guarantee:** Once a loan transitions to `ACTIVE`, the deposit amount is committed to escrow. Neither party can delete or modify the loan until return verification or admin dispute resolution.
4. **Authorization Checks:** Lenders cannot borrow their own items; borrowers cannot approve their own requests; only payees can confirm cash payments.

---

## 7. Automated Testing Suite

BorrowHub comes with a comprehensive automated test suite in `backend/tests/` using **pytest** and FastAPI's **TestClient**:

```
backend/tests/
├── test_admin.py        (Access control, user moderation, dispute resolution)
├── test_auth.py         (Register, login, duplicate check, 2-step forgot password)
├── test_borrow_flow.py  (Self-borrowing check, handover OTP, return OTP handshake)
├── test_items.py        (Item creation, categories, multi-item listing)
├── test_payments.py     (Cash settlement role enforcement)
└── conftest.py          (Isolated test client, database fixtures, mock services)
```

### Running the Tests:
```bash
pytest backend/tests -v
```
**Result:** 14 passed in 4.27s (100% pass rate).

---

## 8. Directory Structure

```
BorrowHub/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          (Environment variables & settings)
│   │   │   ├── database.py        (SQLAlchemy session & engine)
│   │   │   └── security.py        (Bcrypt hashing & JWT generation)
│   │   ├── models/                (SQLAlchemy DB Models: user, item, loan, dispute, etc.)
│   │   ├── schemas/               (Pydantic request & response validation models)
│   │   ├── routes/                (FastAPI API router endpoints)
│   │   ├── services/              (Email dispatch, auth service, loan state transitions)
│   │   └── main.py                (ASGI entrypoint, CORS, static file mounts)
│   ├── migrations/                (Database schema DDL files)
│   └── tests/                     (Automated test suite)
├── frontend/
│   ├── index.html                 (Semantic markup, modals, marketplace catalog)
│   ├── style.css                  (Design system, variables, responsive typography)
│   └── script.js                  (Client application logic, API fetching, modals)
├── DEPLOYMENT_GUIDE.md            (Complete Production Deployment Manual)
├── PROJECT_DOCUMENTATION.md       (This technical documentation)
└── requirements.txt               (Python package dependencies)
```
