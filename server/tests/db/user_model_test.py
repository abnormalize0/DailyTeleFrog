import os

import jwt

from src.db.user_model import User


def test_user_model_encode_auth(monkeypatch):
    monkeypatch.setenv('SECRET_KEY', "secret")
    user: User = User("username", "email", "nickname",
                      "password", "avatar", "description")
    user.id = 1
    token, status = user.encode_auth_token()
    assert token is not None

    payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms='HS256')
    assert payload is not None
    assert type(payload) is dict
    assert payload['user_id'] == user.id


def test_user_model_to_json():
    user_dict = {'id': 1, 'username': 'username', 'email': 'email', 'nickname': 'nickname', 'password': 'password',
                 'avatar': None, 'description': None}

    user: User = User(user_dict['username'], user_dict['email'], nickname=user_dict['nickname'],
                      password=user_dict['password'], avatar=user_dict['avatar'], description=user_dict['description'],
                      id=user_dict['id'])
    user_dict['creation_date'] = str(user.creation_date)

    user_json = user.to_json()
    assert user_json is not None
    assert type(user_json) is dict
    assert user_dict == user_json
