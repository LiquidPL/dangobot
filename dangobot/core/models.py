from django.db import models


class Guild(models.Model):
    """A model for storing settings for a single Discord guild."""
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField(max_length=100)
    command_prefix = models.CharField(max_length=5, default="!")
