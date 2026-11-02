# 🚀 BorrowHub SVNIT — Complete Production Deployment Guide

> **Target Platform:** Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat  
> **Applicable For:** Render, Railway, Ubuntu Linux VPS (AWS EC2 / DigitalOcean / Linode)  
> **Components:** FastAPI Backend, MySQL 8 Database, Real SMTP Email Dispatch, Cloudinary Media Storage

---

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Setting Up Real Email Delivery (SMTP)](#2-setting-up-real-email-delivery-smtp)
   - [Option A: Personal Gmail + App Password (Free & Fastest)](#option-a-personal-gmail--app-password)
   - [Option B: Brevo SMTP (Free 300 Emails/Day — Recommended for Cloud)](#option-b-brevo-smtp-free-300-emailsday)
3. [Setting Up a Free Cloud MySQL Database](#3-setting-up-a-free-cloud-mysql-database)
   - [Option 1: Aiven Free Cloud MySQL](#option-1-aiven-free-cloud-mysql)
   - [Option 2: Railway Managed MySQL](#option-2-railway-managed-mysql)
4. [Cloud Image Storage (Cloudinary)](#4-cloud-image-storage-cloudinary)
5. [Deployment Options](#5-deployment-options)
   - [Method 1: Deploying to Render (Free & Easiest)](#method-1-deploying-to-render-free--easiest)
   - [Method 2: Deploying to Railway (One-Click Stack)](#method-2-deploying-to-railway-one-click-stack)
   - [Method 3: Deploying to an Ubuntu Linux VPS (AWS / DigitalOcean)](#method-3-deploying-to-an-ubuntu-linux-vps-aws--digitalocean)
6. [Complete Production Environment Variables Cheat Sheet](#6-complete-production-environment-variables-cheat-sheet)
7. [Post-Deployment Verification & Testing Checklist](#7-post-deployment-verification--testing-checklist)

---

## 1. Pre-Deployment Checklist

Before pushing to the cloud, ensure your local files are clean and tested:
```bash
# 1. Run all tests to ensure 100% pass rate
pytest backend/tests -v

# 2. Check JavaScript syntax
node -c frontend/script.js

# 3. Ensure requirements.txt is up to date
pip freeze > requirements.txt
```

---

## 2. Setting Up Real Email Delivery (SMTP)

Because college/institutional Google Workspace accounts (`@coed.svnit.ac.in`) have third-party App Passwords disabled by institute IT policy, you must configure a dedicated sender to deliver OTPs to students' inboxes.

### Option A: Personal Gmail + App Password

You can use any personal Gmail account (or create a dedicated free account like `svnit.borrowhub@gmail.com`).

1. Log in to your personal Google account.
2. Turn on **2-Step Verification** in [Google Security Settings](https://myaccount.google.com/security).
3. Navigate to **[Google App Passwords](https://myaccount.google.com/apppasswords)**.
4. Under "App name", enter **BorrowHub** and click **Create**.
5. Google will display a **16-character password** (e.g., `abcd efgh ijkl mnop`).
6. Set your environment variables:
   ```env
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT=587
   SMTP_USER="your.email@gmail.com"
   SMTP_PASSWORD="abcdefghijklmnop"
   SMTP_FROM_EMAIL="your.email@gmail.com"
   SMTP_FROM_NAME="BorrowHub SVNIT"
   SMTP_TLS=True
   ```
> **Student Experience:** When a student registers with their roll number email (e.g. `u25cs136@coed.svnit.ac.in`), the OTP arrives in their official SVNIT inbox from **"BorrowHub SVNIT"**.

---

### Option B: Brevo SMTP (Free 300 Emails/Day — Recommended for Cloud)

[Brevo](https://www.brevo.com/) (formerly Sendinblue) provides reliable transactional SMTP for web servers without Google IP restrictions.

1. Sign up for a free account at [brevo.com](https://www.brevo.com/).
2. In your dashboard, click your profile icon at top-right and select **SMTP & API**.
3. Under the **SMTP** tab, click **Generate a new SMTP key**.
4. Set your environment variables:
   ```env
   SMTP_HOST="smtp-relay.brevo.com"
   SMTP_PORT=587
   SMTP_USER="your-brevo-login-email@example.com"
   SMTP_PASSWORD="your-generated-brevo-smtp-key"
   SMTP_FROM_EMAIL="your-verified-email@example.com"
   SMTP_FROM_NAME="BorrowHub SVNIT"
   SMTP_TLS=True
   ```

---

## 3. Setting Up a Free Cloud MySQL Database

When deploying to the cloud, you need a hosted MySQL database reachable by your web application.

### Option 1: Aiven Free Cloud MySQL
1. Sign up for free at [aiven.io](https://aiven.io/).
2. Create a new service: select **MySQL** (Free tier available).
3. Once created, copy the **Service URI**. It looks like:
   `mysql://avnadmin:password@mysql-xyz.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED`
4. In your `.env`, prefix it with `mysql+pymysql://` for SQLAlchemy:
   ```env
   DATABASE_URL="mysql+pymysql://avnadmin:password@mysql-xyz.aivencloud.com:12345/defaultdb?ssl_verify_cert=false"
   ```

### Option 2: Railway Managed MySQL
1. Go to [railway.app](https://railway.app/).
2. Click **New Project** → **Provision MySQL**.
3. In the MySQL service settings, copy the **Private/Public Connection URL**.

---

## 4. Cloud Image Storage (Cloudinary)

For storing photos of items and dispute damage evidence reliably in the cloud:

1. Create a free account at [cloudinary.com](https://cloudinary.com/).
2. Copy your **Cloud Name**, **API Key**, and **API Secret** from the dashboard.
3. Add to your environment variables:
   ```env
   CLOUDINARY_CLOUD_NAME="your_cloud_name"
   CLOUDINARY_API_KEY="your_api_key"
   CLOUDINARY_API_SECRET="your_api_secret"
   ```

*(If Cloudinary credentials are not set, BorrowHub automatically falls back to local disk storage in `backend/static/uploads/`.)*

---

## 5. Deployment Options

### Method 1: Deploying to Render (Free & Easiest)

[Render](https://render.com/) automatically builds and runs FastAPI with zero server maintenance.

#### Step 1: Push Project to GitHub
```bash
git init
git add .
git commit -m "Production release of BorrowHub SVNIT"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/borrowhub.git
git push -u origin main
```

#### Step 2: Create Web Service on Render
1. Log in to [render.com](https://render.com/) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name:** `borrowhub-svnit`
   - **Region:** Singapore (closest to SVNIT Surat for low latency)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`

#### Step 3: Configure Environment Variables
Under the **Environment** tab on Render, add:

| Variable Name | Recommended Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `False` |
| `DATABASE_URL` | `mysql+pymysql://<user>:<pass>@<cloud-host>:3306/<dbname>` |
| `JWT_SECRET_KEY` | *(generate a 32+ character random secret string)* |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `your.personal.email@gmail.com` |
| `SMTP_PASSWORD` | `your-16-char-app-password` |
| `SMTP_FROM_EMAIL` | `your.personal.email@gmail.com` |
| `SMTP_FROM_NAME` | `BorrowHub SVNIT` |
| `SMTP_TLS` | `True` |
| `CORS_ORIGINS` | `["*"]` |

4. Click **Deploy Web Service**. Render will provision your app and give you a free live URL:  
   `https://borrowhub-svnit.onrender.com`

---

### Method 2: Deploying to Railway (One-Click Stack)

1. Sign up on [railway.app](https://railway.app/).
2. Click **New Project** → **Provision MySQL** (instant database).
3. In the same project canvas, click **New** → **GitHub Repo** → select `borrowhub`.
4. In the web service settings, link the database:
   - `DATABASE_URL` = `${{MySQL.MYSQL_URL}}`
5. Add your SMTP credentials and `ENVIRONMENT="production"`.
6. Click **Settings** → **Generate Domain**. Railway provisions HTTPS instantly.

---

### Method 3: Deploying to an Ubuntu Linux VPS (AWS / DigitalOcean)

For maximum speed, custom SVNIT domain names, and dedicated resources:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv mysql-server nginx git certbot python3-certbot-nginx

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/borrowhub.git /var/www/borrowhub
cd /var/www/borrowhub

# 3. Create virtual environment & install requirements
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure production environment file
cp backend/.env.example backend/.env
nano backend/.env  # edit with your DB & SMTP credentials

# 5. Create Systemd Service for auto-restart
sudo nano /etc/systemd/system/borrowhub.service
```

Paste the following systemd service configuration:
```ini
[Unit]
Description=BorrowHub FastAPI Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/borrowhub
EnvironmentFile=/var/www/borrowhub/backend/.env
ExecStart=/var/www/borrowhub/venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable borrowhub
sudo systemctl start borrowhub
sudo systemctl status borrowhub
```

#### Nginx Reverse Proxy Configuration:
```bash
sudo nano /etc/nginx/sites-available/borrowhub
```

Paste:
```nginx
server {
    server_name borrowhub.svnit.ac.in;  # or your custom domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site & obtain SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/borrowhub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d borrowhub.svnit.ac.in
```

---

## 6. Complete Production Environment Variables Cheat Sheet

```env
# Platform Mode
PROJECT_NAME="BorrowHub"
VERSION="2.0.0"
ENVIRONMENT="production"
DEBUG=False
PORT=8000
HOST="0.0.0.0"

# Cloud Database Connection
DATABASE_URL="mysql+pymysql://<user>:<password>@<host>:3306/<database>?charset=utf8mb4"

# JWT Token Security (Use a long random 32+ character string)
JWT_SECRET_KEY="replace-with-a-unique-random-secret"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OTP_EXPIRY_MINUTES=15

# Real SMTP Email Dispatch (Gmail App Password or Brevo)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-16-char-app-password"
SMTP_FROM_EMAIL="your-email@gmail.com"
SMTP_FROM_NAME="BorrowHub SVNIT"
SMTP_TLS=True

# Designated Campus Dispute Mediators
ADMIN_EMAILS=["u25cs136@coed.svnit.ac.in","admin@svnit.ac.in"]

# Optional Cloudinary Storage
CLOUDINARY_CLOUD_NAME=""
CLOUDINARY_API_KEY=""
CLOUDINARY_API_SECRET=""
```

---

## 7. Post-Deployment Verification & Testing Checklist

After your deployment URL is live, perform this end-to-end audit:

- [ ] **1. Website Reachability:** Visit `https://your-domain.com`. The homepage and listings load with HTTPS.
- [ ] **2. Real Student Sign-Up:** Register with an `@svnit.ac.in` student address. Verify that the 6-digit OTP arrives in the student's real inbox within 10 seconds.
- [ ] **3. Security Check:** Confirm the verification code is **not** displayed anywhere on screen or in browser console.
- [ ] **4. Two-Step Forgot Password:**
  - Click **Forgot password?** → enter your email → click **Send Reset Code →**.
  - Check that the next screen shows **only** the 6-digit verification input without password fields.
  - Enter code and verify. Confirm the password creation fields open up. Set a new password and sign in.
- [ ] **5. Multi-Item Publishing:** Publish 2 or more different items from the same student account. Confirm both appear in the marketplace.
- [ ] **6. In-Person Handover Verification:** Request an item from another account. Have the owner enter the borrower's 6-digit Handover OTP to activate the loan.
- [ ] **7. Return & Deposit Release:** Complete the return by entering the Return OTP. Confirm deposit custody is released.
