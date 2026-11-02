import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger("borrowhub.database")

Base = declarative_base()


def is_placeholder_url(url: str) -> bool:
    if not url:
        return True
    return any(p in url for p in ["<user>", "<password>", "<host>", "<database>"])


def create_app_engine():
    db_url = settings.DATABASE_URL.strip() if settings.DATABASE_URL else ""

    # If DATABASE_URL is unconfigured or contains template placeholders, use persistent local SQLite
    if is_placeholder_url(db_url):
        logger.warning("DATABASE_URL contains unconfigured placeholders (%s). Initializing persistent local database.", db_url)
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "borrowhub_dev.db")
        return create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )

    # Attempt MySQL connection (production or local MySQL instance)
    try:
        connect_args = {}
        if "ssl_ca" not in db_url and "aivencloud.com" in db_url:
            connect_args["ssl"] = {"check_hostname": False}

        eng = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            echo=False,
            connect_args=connect_args,
        )
        # Test connection immediately
        with eng.connect() as conn:
            pass
        logger.info("Successfully connected to primary database at %s", db_url.split("@")[-1] if "@" in db_url else "database")
        return eng
    except Exception as exc:
        logger.warning(
            "Could not connect to configured primary DATABASE_URL (%s). Falling back to persistent local SQLite to keep the service operational: %s",
            type(exc).__name__,
            exc
        )
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "borrowhub_dev.db")
        return create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )


engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_reference_data(session):
    """Seed standard categories and pickup locations if empty."""
    try:
        from backend.app.models.catalog import Category, PickupLocation

        if session.query(Category).count() == 0:
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
            session.commit()

        if session.query(PickupLocation).count() == 0:
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
            session.commit()
    except Exception as e:
        logger.warning("Could not auto-seed reference data: %s", e)
        session.rollback()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
