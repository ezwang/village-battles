from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

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

    _wood = models.IntegerField(default=settings.STARTING_RESOURCES)
    _clay = models.IntegerField(default=settings.STARTING_RESOURCES)
    _iron = models.IntegerField(default=settings.STARTING_RESOURCES)

    _update = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("x", "y"),)


class Building(models.Model):
    CHOICES = (
        ("HQ", "Headquarters"),
        ("WM", "Wood Mine"),
        ("CM", "Clay Mine"),
        ("IM", "Iron Mine"),
        ("WH", "Warehouse"),
    )
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=CHOICES, default="HQ")
    level = models.IntegerField(default=1)

    @property
    def url(self):
        if self.type == "HQ":
            return reverse("hq", kwargs={"village_id": self.village.id})

    class Meta:
        unique_together = (("village", "type"),)
