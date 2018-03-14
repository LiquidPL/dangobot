from django.db import models
from django.utils.text import slugify

def file_path(instance, filename):
    return 'responder/{server_id}/{trigger}'.format(server_id=instance.server.id, trigger=filename)

class Command(models.Model):
    server = models.ForeignKey('db.Server', on_delete=models.CASCADE)
    trigger = models.TextField(max_length=2000)
    response = models.TextField(max_length=2000, blank=True)
    file = models.FileField(upload_to=file_path, blank=True)

    class Meta:
        unique_together = ('server', 'trigger')

    def __str__(self):
        return self.trigger

