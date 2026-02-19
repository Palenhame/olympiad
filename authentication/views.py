import copy

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.serializers import LoginSerializer, RegisterSerializer
from django.conf import settings


def render_login_page(request):
    return render(request, 'login.html')


def set_jwt_cookies(response, access_token, refresh_token):
    cookie_settings = {
        'httponly': True,
        'secure': not settings.DEBUG,  # True в продакшене
        'samesite': 'Lax',
    }
    response.set_cookie(
        key='access',
        value=str(access_token),
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        **cookie_settings,
    )
    response.set_cookie(
        key='refresh',
        value=str(refresh_token),
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        **cookie_settings,
    )
    return response


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            response = Response({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            }, status=status.HTTP_200_OK)

            return set_jwt_cookies(response, refresh.access_token, refresh)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            response = Response({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            }, status=status.HTTP_201_CREATED)

            return set_jwt_cookies(response, refresh.access_token, refresh)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            set_jwt_cookies(response, response.data['access'], response.data['refresh'])
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        if 'refresh' not in request.data and 'refresh' in request.COOKIES:
            data = copy.copy(request.data)
            data['refresh'] = request.COOKIES['refresh']
            request._full_data = data

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            set_jwt_cookies(response, response.data['access'], response.data.get('refresh', ''))
            response.data = {'detail': 'Токен обновлён'}
        return response