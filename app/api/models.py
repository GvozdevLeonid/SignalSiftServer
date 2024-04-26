from django.conf import settings
from django.db import models
import uuid


class UserData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False)
    files = models.JSONField(default=dict, blank=True)
    user_uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = 'User data'
        verbose_name_plural = 'User\'s data'

    def __str__(self):
        return f'User: {self.user.username}, storage {self.user_uuid}'


class UserAlerts(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False)
    alerts = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'User alerts'
        verbose_name_plural = 'User\'s alerts'

    def __str__(self):
        return f'User: {self.user.username}'
