from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from tasks.models import Subject, Task
from tasks.serializers import SubjectsListSerializer, CurrentTaskSerializer



class ReturnTaskAPIView(APIView):
    def get(self, request, subject_id: int):
        task = get_object_or_404(Task, id=subject_id)
        serializer = CurrentTaskSerializer(task, context={'request': request})
        return Response(serializer.data)


class SubjectsListAPIView(APIView):
    def get(self, request):
        subjects = Subject.objects.prefetch_related('tasks').only('id', 'name')
        serializer = SubjectsListSerializer(subjects, many=True)
        return Response(serializer.data)