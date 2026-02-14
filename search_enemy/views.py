from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def search(request):
    return render(request, 'search.html')


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class SearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})
