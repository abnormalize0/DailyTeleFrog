import pytest
from unittest.mock import patch, MagicMock
from src.repository.user import UserRepository
from src.db.user_model import User
from src.request_status import StatusType


@pytest.fixture
def mock_engine():
    with patch('src.repository.user.create_engine') as mock_engine:
        yield mock_engine


@pytest.fixture
def mock_session():
    with patch('src.repository.user.Session') as mock_session:
        yield mock_session


@pytest.fixture
def mock_check_pw_bcrypt():
    with patch('bcrypt.checkpw') as mock_bcrypt:
        yield mock_bcrypt


@pytest.fixture
def mock_hash_pw_bcrypt():
    with patch('bcrypt.hashpw') as mock_bcrypt:
        yield mock_bcrypt


@pytest.fixture
def mock_getenv():
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = '12'
        yield mock_getenv


def test_get_user_by_username_and_password_success(mock_engine, mock_session, mock_check_pw_bcrypt):
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance

    mock_user_instance = MagicMock(spec=User)
    mock_user_instance.password = 'hashed_password'

    mock_session_instance.query.return_value.where.return_value.first.return_value = mock_user_instance
    mock_check_pw_bcrypt.return_value = True

    result, status = UserRepository.get_user('test_user', 'test_pass')
    assert result == mock_user_instance
    assert status.__dict__()['type'] == StatusType.OK.name


def test_get_user_by_username_and_password_user_is_not_found(mock_engine, mock_session, mock_check_pw_bcrypt):
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance

    mock_session_instance.query.return_value.where.return_value.first.return_value = None

    result, status = UserRepository.get_user('test_user', 'test_pass')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == "User is not found"


def test_get_user_by_username_and_password_user_password_is_wrong(mock_engine, mock_session, mock_check_pw_bcrypt):
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance

    mock_user_instance = MagicMock(spec=User)
    mock_session_instance.query.return_value.where.return_value.first.return_value = mock_user_instance
    mock_check_pw_bcrypt.return_value = False

    result, status = UserRepository.get_user('test_user', 'test_pass')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == "User is not found"


def test_save_user_username_password_email_success(mock_engine, mock_session, mock_hash_pw_bcrypt, mock_getenv):
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance

    mock_session_instance.query.return_value.where.return_value.first.return_value = None
    mock_hash_pw_bcrypt.return_value = b'hashed_pw'

    result, status = UserRepository.save_user('test_user', 'test_pass', 'test@example.com')

    assert result.username == 'test_user'
    assert result.password == 'hashed_pw'
    assert result.email == 'test@example.com'
    assert status.__dict__()['type'] == StatusType.OK.name

    mock_session_instance.commit.assert_called_once()


def test_save_user_username_password_email_user_exists(mock_engine, mock_session, mock_hash_pw_bcrypt, mock_getenv):
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance
    mock_user_instance = MagicMock()

    mock_session_instance.query.return_value.where.return_value.first.return_value = mock_user_instance

    result, status = UserRepository.save_user('test_user', 'test_pass', 'test@example.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == 'User with this email already exists'
