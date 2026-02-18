from django.core.paginator import Paginator
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from tasks.models import Subject, Task
from tasks.serializers import SubjectsListSerializer, CurrentTaskSerializer, BaseTaskSerializer


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


class TasksListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subject_id = request.query_params.get('subject_id', '').strip()
        difficulty = request.query_params.get('difficulty', '').strip()

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        queryset = Task.objects.select_related('subject').only(
            'id', 'question', 'subject__id', 'subject__name', 'difficulty'
        )

        if subject_id:
            try:
                queryset = queryset.filter(subject_id=int(subject_id))
            except ValueError:
                pass

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = BaseTaskSerializer(
            page_obj.object_list,
            many=True,
            context={'request': request}
        )

        return Response({
            'items': serializer.data,
            'page': page,
            'items_count': paginator.count,
            'total_pages': paginator.num_pages,
        })