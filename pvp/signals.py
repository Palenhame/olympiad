from django.db.models.signals import post_save
from django.dispatch import receiver

from pvp.models import RoundTask
from pvp.services.pvp_cache import CorrectAnswerCache


@receiver(post_save, sender=RoundTask)
async def post_save_receiver(sender, instance: RoundTask, created, **kwargs):
    if created:
        CorrectAnswerCache.set(
            instance.id,
            instance.order,
        )
