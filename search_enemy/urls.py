from django.urls import path

from .views import SearchAPIView, search

urlpatterns = [
    path('', search, name='render_search_enemy'),
    path('api', SearchAPIView.as_view(), name='search_enemy'),
]
