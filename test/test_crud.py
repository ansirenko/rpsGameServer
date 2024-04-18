import bcrypt
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

import models
import schemas
import crud


@pytest.fixture
def test_db_session():
    session = Mock(spec=Session)
    return session


def test_create_user(test_db_session):
    user_data = schemas.UserCreate(nickname="test_user", password="test_password")

    with patch('bcrypt.gensalt', return_value=b"salt"), \
            patch('bcrypt.hashpw', return_value=b"hashed_password"), \
            patch.object(test_db_session, 'commit'), \
            patch.object(test_db_session, 'refresh'):
        created_user = crud.create_user(test_db_session, user_data)

        assert created_user.nickname == user_data.nickname
        assert created_user.password == "hashed_password"
        assert test_db_session.commit.called
        assert test_db_session.refresh.called


def test_check_password():
    user_password = "test_password"
    stored_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    assert crud.check_password(user_password, stored_password) is True
    assert crud.check_password("wrong_password", stored_password) is False


def test_get_user_by_nickname(test_db_session):
    test_nickname = "example_user"
    mock_user = models.User(nickname=test_nickname)
    test_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    result = crud.get_user_by_nickname(test_db_session, test_nickname)

    test_db_session.query.assert_called_with(models.User)
    test_db_session.query.return_value.filter.assert_called_once()
    assert result == mock_user
    assert result.nickname == test_nickname


def test_get_user(test_db_session):
    test_user_id = 1
    mock_user = models.User(user_id=test_user_id, nickname="example_user")
    test_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    result = crud.get_user(test_db_session, test_user_id)

    test_db_session.query.assert_called_with(models.User)
    test_db_session.query.return_value.filter.assert_called_once()
    assert result == mock_user
    assert result.user_id == test_user_id


def test_get_user_stats(test_db_session):
    test_user_id = 1
    mock_stats = models.GameStat(user_id=test_user_id, wins=5, losses=3, draws=2)
    test_db_session.query.return_value.filter.return_value.first.return_value = mock_stats

    result = crud.get_user_stats(test_db_session, test_user_id)

    test_db_session.query.assert_called_with(models.GameStat)
    test_db_session.query.return_value.filter.assert_called_once()
    assert result == mock_stats
    assert result.user_id == test_user_id
    assert result.wins == 5
    assert result.losses == 3
    assert result.draws == 2
