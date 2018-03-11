from django.db import models

class Server(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.TextField(max_length=100)
