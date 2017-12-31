from django.db import models

from ..game.models import World
from ..users.models import User


class Tribe(models.Model):
    name = models.TextField()
    world = models.ForeignKey(World, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("name", "world"),)


class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tribe = models.ForeignKey(Tribe, on_delete=models.CASCADE)
