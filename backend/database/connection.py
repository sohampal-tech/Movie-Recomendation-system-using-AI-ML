"""
backend/database/connection.py
Production-grade database connection supporting Neon PostgreSQL & SQLite fallback.
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def build_database_url() -> str:
    """Build database connection string from environment variables."""
    # Explicit DATABASE_URL takes priority
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    # Check for Postgres environment variables
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "neondb")

    if db_host and db_user and db_password:
        return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

    # Default fallback: local sqlite database (use /tmp in serverless/read-only environments)
    tmp_dir = "/tmp" if os.path.exists("/tmp") else "data"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
    except Exception:
        pass
    return f"sqlite:///{tmp_dir}/movies.db"


DATABASE_URL = build_database_url()
masked_url = DATABASE_URL
if "@" in masked_url and ":" in masked_url:
    try:
        prefix, rest = masked_url.split("://", 1)
        user_pass, host_db = rest.split("@", 1)
        user = user_pass.split(":")[0]
        masked_url = f"{prefix}://{user}:****@{host_db}"
    except Exception:
        pass

logger.info(f"Connecting to database: {masked_url}")

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    connect_args = {"connect_timeout": 15}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300
    )
except Exception as e:
    logger.warning(f"Failed to create engine with primary URL: {e}. Falling back to SQLite.")
    DATABASE_URL = "sqlite:///data/movies.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency / context helper for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
