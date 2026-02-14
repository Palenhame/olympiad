from rest_framework import serializers


class TrainingTaskSerializer(serializers.Serializer):
    question = serializers.CharField()
    is_correct = serializers.BooleanField(allow_null=True)


class TrainingStateSerializer(serializers.Serializer):
    tasks = TrainingTaskSerializer(many=True)
    solved_count = serializers.IntegerField()