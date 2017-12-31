from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    profile = models.TextField(blank=True)
    tribes = models.ManyToManyField("tribes.Tribe", related_name="members", through="tribes.Member", through_fields=("user", "tribe"))
