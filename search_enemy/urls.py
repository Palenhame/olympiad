from django.urls import path

from .views import SearchAPIView, search

urlpatterns = [path('', search), path('api', SearchAPIView.as_view())]
