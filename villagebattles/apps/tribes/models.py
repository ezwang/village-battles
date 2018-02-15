from django.db import models

from ..game.models import World
from ..users.models import User


class Tribe(models.Model):
    name = models.TextField()
    world = models.ForeignKey(World, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("name", "world"),)


class Member(models.Model):
    OWNER = 'OW'
    MEMBER = 'ME'

    CHOICES = (
        (OWNER, 'Owner'),
        (MEMBER, 'Member')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tribe = models.ForeignKey(Tribe, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=CHOICES)


class Thread(models.Model):
    name = models.TextField()
    tribe = models.ForeignKey(Tribe, on_delete=models.CASCADE, related_name="threads")
