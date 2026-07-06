import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger(__name__)

# Determine if we need SQLite check_same_thread parameters
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.exception("Failed to connect to the database engine.")
    raise e

def get_db():
    """
    Dependency injection generator to provide database session per request.
    Closes session automatically upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
