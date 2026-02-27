import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app

default_test_client = pytest.fixture
def test_client():
    return TestClient(app)

def db_session():
    engine = create_engine('postgresql://user:password@localhost/library')
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()