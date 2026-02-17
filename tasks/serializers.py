from rest_framework import serializers

from tasks.models import Subject, SubjectTheme, Task
from users.models import UserTask


class SubjectsThemesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectTheme
        fields = ['id', 'name']


class SubjectsListSerializer(serializers.ModelSerializer):
    themes = SubjectsThemesListSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'themes']


class CurrentTaskSerializer(serializers.ModelSerializer):
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'question', 'is_correct']

    def get_is_correct(self, obj):
        user = self.context['request'].user

        user_task = UserTask.objects.filter(
            user=user,
            task=obj
        ).only('is_correct').first()

        return user_task.is_correct if user_task is not None else None
