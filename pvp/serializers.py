from enum import StrEnum

from rest_framework import serializers


class MessageType(StrEnum):
    ANSWER = 'answer'
    RESULT = 'result'
    ENEMY_RESULT = 'enemy_result'


class AnswerMessageSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[MessageType.ANSWER])
    task_index = serializers.IntegerField(min_value=0)
    answer = serializers.CharField()


class ResultMessageSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=[MessageType.RESULT, MessageType.ENEMY_RESULT]
    )
    task_index = serializers.IntegerField(min_value=0)
    is_correct = serializers.BooleanField(allow_null=True)


class RoundTaskSerializer(serializers.Serializer):
    question = serializers.CharField()
    is_correct = serializers.BooleanField()


class RoundTaskStatusSerializer(serializers.Serializer):
    question = serializers.CharField()
    user_is_correct = serializers.BooleanField(allow_null=True)
    enemy_is_correct = serializers.BooleanField(allow_null=True)


class RoundStateSerializer(serializers.Serializer):
    tasks = RoundTaskStatusSerializer(many=True)
    user_solved_count = serializers.IntegerField()
    enemy_solved_count = serializers.IntegerField()
