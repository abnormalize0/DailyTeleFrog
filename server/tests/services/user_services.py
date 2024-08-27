import json
from unittest.mock import patch, MagicMock
from src.db.user_model import User
from src.services.user_service import UserService
from src.request_status import Status, StatusType, ErrorType


@patch('src.repository.user.UserRepository.get_user')
def test_login_success(mock_get_user):

    mock_user = MagicMock(spec=User)
    mock_user.encode_auth_token.return_value = ('fake_auth_token', None)
    mock_user.to_json.return_value = {'username': 'test_user'}

    mock_get_user.return_value = (mock_user, None)

    result, status = UserService.login('test_user', 'test_pass')

    expected_result = json.dumps({
        "user": {'username': 'test_user'},
        "auth_token": 'fake_auth_token'
    })

    assert result == expected_result
    assert status.__dict__()['type'] == StatusType.OK.name
    mock_get_user.assert_called_once_with('test_user', 'test_pass')


def test_login_username_none():
    result, status = UserService.login(None, 'test_pass')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name


def test_login_password_none():
    result, status = UserService.login('test_user', None)

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name


@patch('src.repository.user.UserRepository.get_user')
def test_login_user_is_not_found(mock_get_user):
    mock_get_user.return_value = (None, Status(StatusType.ERROR, error_type=ErrorType.ValueError))

    result, status = UserService.login('test_user', 'test_pass')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    mock_get_user.assert_called_once_with('test_user', 'test_pass')


@patch('src.repository.user.UserRepository.get_user')
def test_login_user_auth_token_not_encoded(mock_get_user):
    mock_user = MagicMock(spec=User)
    mock_user.encode_auth_token.return_value = (None, Status(StatusType.ERROR, error_type=ErrorType.ValueError))

    mock_get_user.return_value = (mock_user, None)

    result, status = UserService.login('test_user', 'test_pass')

    expected_result = json.dumps({
        "user": None,
        "auth_token": None
    })

    assert result == expected_result
    assert status.__dict__()['type'] == StatusType.ERROR.name


@patch('src.repository.user.UserRepository.save_user')
def test_register_success(mock_save_user):
    mock_user = MagicMock(spec=User)
    mock_user.encode_auth_token.return_value = ('fake_auth_token', None)
    mock_user.to_json.return_value = {'username': 'test_user'}

    mock_save_user.return_value = (mock_user, None)

    result, status = UserService().register('test_user', 'W3#j9$HlQ', 'email@gmail.com')

    expected_result = json.dumps({
        "user": {'username': 'test_user'},
        "auth_token": 'fake_auth_token'
    })

    assert result == expected_result
    assert status.__dict__()['type'] == StatusType.OK.name
    mock_save_user.assert_called_once_with('test_user', 'W3#j9$HlQ', 'email@gmail.com')


def test_register_username_none():
    result, status = UserService().register(None, 'test_pass', 'email@email.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name


def test_register_password_none():
    result, status = UserService().register('test_user', None, 'email@email.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name


def test_register_email_none():
    result, status = UserService().register('test_user', 'test_pass', None)

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name


def test_register_username_is_not_compliant():
    result, status = UserService().register('12_', 'test_pass', 'email@gmail.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == 'The username format is not compliant'


def test_register_password_is_not_compliant():
    result, status = UserService().register('test_user', 'test_pass', 'email@gmail.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == 'The password format is not compliant'


def test_register_email_is_not_compliant():
    result, status = UserService().register('test_user', 'W3#j9$HlQ', 'test')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    assert status._msg == 'The email format is not compliant'


@patch('src.repository.user.UserRepository.save_user')
def test_register_user_is_not_saved(mock_save_user):
    mock_save_user.return_value = (None, Status(StatusType.ERROR, error_type=ErrorType.ValueError))

    result, status = UserService().register('test_user', 'W3#j9$HlQ', 'email@gmail.com')

    assert result is None
    assert status.__dict__()['type'] == StatusType.ERROR.name
    mock_save_user.assert_called_once_with('test_user', 'W3#j9$HlQ', 'email@gmail.com')


@patch('src.repository.user.UserRepository.save_user')
def test_register_token_is_not_generated(mock_save_user):
    mock_user = MagicMock(spec=User)
    mock_user.encode_auth_token.return_value = (None, Status(StatusType.ERROR, error_type=ErrorType.ValueError))

    mock_save_user.return_value = (mock_user, None)

    result, status = UserService().register('test_user', 'W3#j9$HlQ', 'email@gmail.com')

    expected_result = json.dumps({
        "user": None,
        "auth_token": None
    })

    assert result == expected_result
    assert status.__dict__()['type'] == StatusType.ERROR.name
    mock_save_user.assert_called_once_with('test_user', 'W3#j9$HlQ', 'email@gmail.com')
