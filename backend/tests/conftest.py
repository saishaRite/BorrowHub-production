import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
settings.ENVIRONMENT = "test"

from backend.app.core.database import Base, get_db
import backend.app.models
from backend.app.models.user import AppUser
from backend.app.models.catalog import Category, PickupLocation, Item, ItemImage
from backend.app.core.security import hash_password
from backend.app.main import app

# In-memory SQLite for self-contained, isolated test execution
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Categories (8 categories)
    categories = [
        Category(category_id=1, category_name="Books", category_description="Textbooks, reference books and novels"),
        Category(category_id=2, category_name="Electronics", category_description="Calculators, Arduino kits, chargers, cables and gadgets"),
        Category(category_id=3, category_name="Lab Equipment", category_description="Lab coats, drafters, multimeters, kits and instruments"),
        Category(category_id=4, category_name="Sports", category_description="Bats, rackets, balls and fitness gear"),
        Category(category_id=5, category_name="Tools", category_description="Hand tools, soldering irons and hardware"),
        Category(category_id=6, category_name="Stationery", category_description="Pens, drawing sheets and project supplies"),
        Category(category_id=7, category_name="Musical Instruments", category_description="Guitars, keyboards and accessories"),
        Category(category_id=8, category_name="Others", category_description="Miscellaneous campus utility items"),
    ]
    for c in categories:
        session.merge(c)

    # Pickup locations (7 locations)
    locations = [
        PickupLocation(location_id=1, name="Bhabha Bhavan", description="Bhabha Bhavan Hostel Main Gate / Reception"),
        PickupLocation(location_id=2, name="Gajjar Bhavan", description="Gajjar Bhavan Hostel Main Gate / Reception"),
        PickupLocation(location_id=3, name="Swami Vivekanand Bhavan", description="SVB Hostel Main Entrance"),
        PickupLocation(location_id=4, name="Mother Teresa Bhavan", description="MTB Hostel Main Entrance"),
        PickupLocation(location_id=5, name="CSE Department", description="Computer Science & Engineering Ground Floor Lobby"),
        PickupLocation(location_id=6, name="Central Library", description="SVNIT Central Library Entrance"),
        PickupLocation(location_id=7, name="Main Gate / SAC", description="Student Activity Centre / Main Gate Security Cabin"),
    ]
    for l in locations:
        session.merge(l)

    # Users
    hashed = hash_password("Svnit@2026!")
    users = [
        AppUser(user_id=1, roll_number="U23CS001", full_name="Aarav Patel", svnit_email="u23cs001@svnit.ac.in", phone="+919876543210", hostel_or_dept="Bhabha Bhavan", password_hash=hashed, role="STUDENT", is_verified=1, is_active=1),
        AppUser(user_id=2, roll_number="U23CS002", full_name="Priya Shah", svnit_email="u23cs002@svnit.ac.in", phone="+919876543211", hostel_or_dept="Mother Teresa Bhavan", password_hash=hashed, role="STUDENT", is_verified=1, is_active=1),
        AppUser(user_id=3, roll_number="U23CS003", full_name="Rohan Mehta", svnit_email="u23cs003@svnit.ac.in", phone="+919876543212", hostel_or_dept="Gajjar Bhavan", password_hash=hashed, role="STUDENT", is_verified=1, is_active=1),
        AppUser(user_id=4, roll_number="ADMIN001", full_name="Campus Administrator", svnit_email="admin@svnit.ac.in", phone="+919876543299", hostel_or_dept="Central Administration", password_hash=hashed, role="ADMIN", is_verified=1, is_active=1),
    ]
    for u in users:
        session.merge(u)

    # Default item 1 owned by student 1
    item1 = Item(
        item_id=1,
        owner_id=1,
        category_id=2,
        location_id=1,
        title="Casio FX-991EX Classwiz Scientific Calculator",
        description="Ideal for engineering mathematics, matrices, equations and scientific computations.",
        item_condition="NEW",
        deposit_amount=Decimal("300.00"),
        daily_fee=Decimal("15.00"),
        max_borrow_days=7,
        listing_status="ACTIVE",
    )
    session.merge(item1)
    img1 = ItemImage(
        image_id=1,
        item_id=1,
        image_url="https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=600&auto=format&fit=crop&q=80",
        sort_order=0,
        is_primary=1,
    )
    session.merge(img1)

    session.commit()
    session.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_headers_student_a(client):
    res = client.post("/api/auth/login", json={
        "email": "u23cs001@svnit.ac.in",
        "password": "Svnit@2026!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_student_b(client):
    res = client.post("/api/auth/login", json={
        "email": "u23cs002@svnit.ac.in",
        "password": "Svnit@2026!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@svnit.ac.in",
        "password": "Svnit@2026!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
