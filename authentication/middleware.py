from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


def get_token_from_scope(scope):
    headers = dict(scope.get('headers', []))
    cookie_header = headers.get(b'cookie', b'').decode()

    for chunk in cookie_header.split(';'):
        chunk = chunk.strip()
        if chunk.startswith('access='):
            return chunk[len('access='):]

    query_string = scope.get('query_string', b'').decode()
    params = parse_qs(query_string)
    if 'token' in params:
        return params['token'][0]

    return None


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = get_token_from_scope(scope)
        print("scope query_string:", scope.get('query_string'))
        print("scope headers:", scope.get('headers'))
        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)