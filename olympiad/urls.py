from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('search_enemy/', include('search_enemy.urls')),
    path('pvp/', include('pvp.urls')),
    path('auth/', include('authentication.urls')),
    path("users/", include('users.urls')),
    path('trainings/', include('trainings.urls')),
    path('tasks/', include('tasks.urls')),
] + debug_toolbar_urls()
