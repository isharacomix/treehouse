from django.db import models

from django.contrib.auth.models import User

from uuid import uuid4


class Invite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    expires = models.DateTimeField()
    expired = models.BooleanField(default=False)
