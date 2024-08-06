from flask import request, Response, g
from functools import wraps
from src.request_status import Status, StatusType
import jwt
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]

        if not token:
            return Response(status=401)

        try:
            payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms='HS256')
            g.current_user = payload['user_id']
        except jwt.ExpiredSignatureError:
            return None, Status(StatusType.ERROR, msg='Signature expired. Please log in again.')
        except jwt.InvalidTokenError:
            return None, Status(StatusType.ERROR, msg='Please log in again.')

        return f(*args, **kwargs)

    return decorated