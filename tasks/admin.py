from django.contrib import admin

from tasks.models import Task, TaskTag, TaskSource, Subject, SubjectTheme

admin.site.register(Task)
admin.site.register(TaskSource)
admin.site.register(TaskTag)
admin.site.register(Subject),
admin.site.register(SubjectTheme)
