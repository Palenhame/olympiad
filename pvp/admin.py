from django.contrib import admin

from pvp.models import Round, RoundTask, RoundPlayer

# Register your models here.
admin.site.register(Round)
admin.site.register(RoundTask)
admin.site.register(RoundPlayer)
