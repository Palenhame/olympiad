from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
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


@database_sync_to_async
def refresh_access_token(refresh_token):
    try:
        refresh = RefreshToken(refresh_token)
        return str(refresh.access_token)
    except TokenError:
        return None


def get_tokens_from_scope(scope):
    headers = dict(scope.get('headers', []))
    cookie_header = headers.get(b'cookie', b'').decode()

    cookies = {}
    for chunk in cookie_header.split(';'):
        chunk = chunk.strip()
        if '=' in chunk:
            key, value = chunk.split('=', 1)
            cookies[key.strip()] = value.strip()

    access = cookies.get('access')
    refresh = cookies.get('refresh')

    if not access:
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        access = params.get('token', [None])[0]

    return access, refresh


class AllowAllOriginsMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        return await self.inner(scope, receive, send)


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        access_token, refresh_token = get_tokens_from_scope(scope)

        user = AnonymousUser()

        if access_token:
            user = await get_user_from_token(access_token)

        if not user.is_authenticated and refresh_token:
            new_access = await refresh_access_token(refresh_token)
            if new_access:
                user = await get_user_from_token(new_access)

        scope['user'] = user
        return await super().__call__(scope, receive, send)



class AutoRefreshJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get('access')
        refresh_token = request.COOKIES.get('refresh')

        if access_token:
            try:
                AccessToken(access_token)
            except TokenError:
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        request.COOKIES['access'] = str(refresh.access_token)
                        request._new_access_token = str(refresh.access_token)
                    except TokenError:
                        request._logout = True

        response = self.get_response(request)

        cookie_settings = {
            'httponly': True,
            'secure': not settings.DEBUG,
            'samesite': 'Lax',
        }

        if hasattr(request, '_new_access_token'):
            response.set_cookie(
                key='access',
                value=request._new_access_token,
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                **cookie_settings,
            )

        if hasattr(request, '_logout'):
            response.delete_cookie('access')
            response.delete_cookie('refresh')

        return response