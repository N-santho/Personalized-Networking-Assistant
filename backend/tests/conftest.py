import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool
from backend.app import app
from backend.database import Base, get_db

@pytest.fixture(name="db_session", scope="function")
def db_session_fixture():
    """
    Creates a fresh, in-memory SQLite database for each test function to
    ensure isolation and side-effect-free runs. Uses StaticPool to share
    the in-memory database connection across threads.
    """
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(name="client", scope="function")
def client_fixture(db_session):
    """
    Returns a FastAPI TestClient configured to override the database
    dependency with the isolated test session database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    # Inject database override
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
        
    # Clear override after test run is complete
    app.dependency_overrides.clear()
