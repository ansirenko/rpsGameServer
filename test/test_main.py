import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base

from main import app, get_db

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost/rock_paper_scissors"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    _client = TestClient(app)
    yield _client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(client):
    connection = engine.connect()
    transaction = connection.begin()
    _db_session = TestingSessionLocal(bind=connection)
    app.dependency_overrides[get_db] = lambda: _db_session

    yield _db_session

    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


def test_create_user(client, db_session):
    response = client.post(
        "/users/",
        json={"nickname": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['nickname'] == "testuser"
    user = db_session.query(models.User).filter_by(nickname="testuser").first()
    assert user is not None


def test_get_user(client, db_session):
    user = models.User(nickname="testuser2", password="testpass")
    db_session.add(user)
    db_session.commit()

    user_id = user.user_id
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['user_id'] == user_id


def test_get_user_stats_found(client, db_session):
    user = models.User(nickname="test_get_user_stats_found", password="test_get_user_stats_found")
    db_session.add(user)
    db_session.commit()

    stat = models.GameStat(user_id=user.user_id, wins=5, losses=3, draws=2)
    db_session.add(stat)
    db_session.commit()

    response = client.get(f"/stats/{user.user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["wins"] == 5
    assert data["losses"] == 3
    assert data["draws"] == 2


def test_get_user_stats_not_found(client, db_session):
    user_id = 999
    response = client.get(f"/stats/{user_id}")
    assert response.status_code == 404


def test_login_user_not_found(client, db_session):
    response = client.post("/login/", json={"nickname": "nonexistentuser", "password": "any"})
    assert response.status_code == 404


def test_login_incorrect_password(client, db_session):
    hashed_password = bcrypt.hashpw("test_login_incorrect_password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = models.User(nickname="test_login_incorrect_password", password=hashed_password)
    db_session.add(user)
    db_session.commit()

    response = client.post("/login/", json={"nickname": "test_login_incorrect_password", "password": "wrongpassword"})
    assert response.status_code == 403


def test_login_successful(client, db_session):
    hashed_password = bcrypt.hashpw("test_login_successful".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = models.User(nickname="test_login_successful", password=hashed_password)
    db_session.add(user)
    db_session.commit()

    response = client.post("/login/", json={"nickname": "test_login_successful", "password": "test_login_successful"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["nickname"] == "test_login_successful"
    assert data["message"] == "Login successful"
