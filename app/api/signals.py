from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from api import models


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wishlist(sender, instance, created, **kwargs):
    if created:
        models.UserData.objects.create(user=instance)
        models.UserAlerts.objects.create(user=instance)
