from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        raw_token = request.COOKIES.get('access')

        if raw_token is None:
            return super().authenticate(request)

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        try:
            user = self.get_user(validated_token)
        except AuthenticationFailed:
            raise

        return user, validated_token