from django.contrib import admin

from tasks.models import Task, TaskTag, TaskSource

admin.site.register(Task)
admin.site.register(TaskSource)
admin.site.register(TaskTag)
