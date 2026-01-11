from django.contrib import admin

from tasks.models import Task, TaskTag, TaskSource

# Register your models here.
admin.site.register(Task)
admin.site.register(TaskSource)
admin.site.register(TaskTag)
