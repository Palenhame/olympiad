from django.urls import path
from authentication.views import LoginAPIView, RegisterAPIView, CookieTokenRefreshView, CookieTokenObtainPairView, render_login_page

urlpatterns = [
    path('', render_login_page, name='render_login'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]
