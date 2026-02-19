from django.db.models import Avg, Count, Q
from rest_framework import serializers
from users.models import User


class UserStatsSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'stats']

    def get_stats(self, user):
        train_stats = user.training_statistics.aggregate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_speed=Avg('time_to_solve'),
        )

        pvp_stats = user.round_statistics.aggregate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_speed=Avg('time_to_solve'),
        )

        train_total = train_stats['total'] or 0
        train_correct = train_stats['correct'] or 0
        pvp_total = pvp_stats['total'] or 0
        pvp_correct = pvp_stats['correct'] or 0
        total = train_total + pvp_total

        return {
            'rate': user.rating,
            'trains_count': train_total,
            'pvp_count': pvp_total,
            'accuracy_train': round(train_correct / train_total * 100, 1) if train_total else 0,
            'accuracy_pvp': round(pvp_correct / pvp_total * 100, 1) if pvp_total else 0,
            'accuracy_total': round((train_correct + pvp_correct) / total * 100, 1) if total else 0,
            'speed_train': round(train_stats['avg_speed'] or 0, 2),
            'speed_pvp': round(pvp_stats['avg_speed'] or 0, 2),
            'speed_total': round(
                ((train_stats['avg_speed'] or 0) * train_total + (pvp_stats['avg_speed'] or 0) * pvp_total) / total, 2
            ) if total else 0,
        }