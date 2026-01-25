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
    type = serializers.ChoiceField(choices=[MessageType.RESULT, MessageType.ENEMY_RESULT])
    task_index = serializers.IntegerField(min_value=0)
    is_correct = serializers.BooleanField()
