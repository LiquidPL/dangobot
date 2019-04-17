from django.db import models


class Guild(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField(max_length=100)
    command_prefix = models.CharField(max_length=5, default="!")
