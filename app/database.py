import os
import pathlib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    db_path = pathlib.Path(__file__).parent.parent / "raseel_dev.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://raseel_user:raseel_secure_2026@localhost:5432/raseel_db"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_tables():
    from app.models import business, conversation, customer, product, order, consent
    from app.models import user
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
