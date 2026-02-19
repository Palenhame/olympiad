# users/views.py
from django.shortcuts import render
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from users.models import User
from users.serializers import UserStatsSerializer


class UserStatsApiView(RetrieveAPIView):
    serializer_class = UserStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk:
            return User.objects.get(pk=pk)
        return self.request.user


def render_profile_page(request):
    return render(request, 'profile.html')