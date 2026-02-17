from django.contrib import admin

from user_statistics.models import RoundStatistics, TrainingStatistics

admin.site.register(RoundStatistics)
admin.site.register(TrainingStatistics)
