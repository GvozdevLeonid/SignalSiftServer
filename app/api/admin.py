from django.contrib import admin
from api import models

admin.site.register(models.UserData)
admin.site.register(models.UserAlerts)
