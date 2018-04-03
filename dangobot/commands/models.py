from django.db import models


def file_path(instance, filename):
    return 'commands/{guild_id}/{trigger}'.format(
        guild_id=instance.guild.id, trigger=filename
    )


class Command(models.Model):
    guild = models.ForeignKey('core.Guild', on_delete=models.CASCADE)
    trigger = models.TextField(max_length=2000)
    response = models.TextField(max_length=2000, blank=True)
    file = models.FileField(upload_to=file_path, blank=True)

    class Meta:
        unique_together = ('guild', 'trigger')

    def __str__(self):
        return '[{0.guild.name}] {0.trigger} -> {0.response}'.format(self)
