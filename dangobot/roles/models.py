from django.db import models

# Create your models here.


class RoleForVoiceChannel(models.Model):
    """
    Contains configuration for roles linked with voice channels.
    """

    # while the guild id can be inferred from from the voice channel/role,
    # we're including it here to avoid unnecessary discord api queries when
    # looking up stuff in the database
    guild_id = models.BigIntegerField()
    voice_channel_id = models.BigIntegerField()
    role_id = models.BigIntegerField()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        # see https://github.com/microsoft/pylance-release/issues/3814
        unique_together = ("voice_channel_id", "role_id")
