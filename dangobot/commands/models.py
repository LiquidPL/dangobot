import uuid

from django.db import models

from dangobot.core.models import Guild


def file_path(instance, filename):
    """Returns the path in which the command attachments should be stored."""

    return "commands/{guild_id}/{id}_{trigger}".format(
        guild_id=instance.guild.id, id=uuid.uuid4(), trigger=filename
    )


class Command(models.Model):
    """Stores custom commmands configured by the users."""

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    trigger = models.TextField(max_length=2000)
    response = models.TextField(max_length=2000, blank=True)
    file = models.FileField(upload_to=file_path, max_length=300, blank=True)
    original_file_name = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ("guild", "trigger")

    def __str__(self):
        return "[{0.guild.name}] {0.trigger} -> {0.response}".format(self)
