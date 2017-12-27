from django.db import models

from ..users.models import User


class World(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name


class Village(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    name = models.TextField()
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("x", "y"),)
