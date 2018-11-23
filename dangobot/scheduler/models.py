from django.db import models
from django.contrib.postgres.fields import JSONField


class Task(models.Model):
    plugin = models.CharField(max_length=100)
    method = models.CharField(max_length=100)
    args = JSONField()
    kwargs = JSONField()

    scheduled_time = models.DateTimeField()
