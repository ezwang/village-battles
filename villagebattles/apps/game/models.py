from decimal import Decimal

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

    _wood = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)
    _clay = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)
    _iron = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)

    _update = models.DateTimeField(default=timezone.now)

    @property
    def max_capacity(self):
        return int(1000 * 1.2**(self.building_set.get(type="WH").level - 1))

    @property
    def population(self):
        return sum([x.population for x in self.building_set.all()])

    @property
    def max_population(self):
        return int(200 * 1.2**(self.building_set.get(type="FM").level - 1))

    def _do_resource_update(self):
        if hasattr(self, "_done_resource_update"):
            return
        self._done_resource_update = True
        now = timezone.now()
        diff = (now - self._update)
        diff = int(diff.total_seconds()) + (diff.microseconds / Decimal(1000000))
        self.wood = self._wood + (diff / Decimal(3600)) * self.wood_rate
        self.clay = self._clay + (diff / Decimal(3600)) * self.clay_rate
        self.iron = self._iron + (diff / Decimal(3600)) * self.iron_rate
        self._update = now
        self.save()

    @property
    def wood(self):
        self._do_resource_update()
        return int(self._wood)

    @property
    def clay(self):
        self._do_resource_update()
        return int(self._clay)

    @property
    def iron(self):
        self._do_resource_update()
        return int(self._iron)

    @property
    def wood_rate(self):
        """ How much wood should be produced every hour. """
        return int(30 * 1.2**(self.building_set.get(type="WM").level - 1))

    @property
    def clay_rate(self):
        """ How much clay should be produced every hour. """
        return int(30 * 1.2**(self.building_set.get(type="CM").level - 1))

    @property
    def iron_rate(self):
        """ How much iron should be produced every hour. """
        return int(30 * 1.2**(self.building_set.get(type="IM").level - 1))

    @wood.setter
    def wood(self, x):
        self._wood = min(x, self.max_capacity)

    @clay.setter
    def clay(self, x):
        self._clay = min(x, self.max_capacity)

    @iron.setter
    def iron(self, x):
        self._iron = min(x, self.max_capacity)

    class Meta:
        unique_together = (("x", "y"),)


class Building(models.Model):
    CHOICES = (
        ("HQ", "Headquarters"),
        ("WM", "Wood Mine"),
        ("CM", "Clay Mine"),
        ("IM", "Iron Mine"),
        ("WH", "Warehouse"),
        ("FM", "Farm"),
    )
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=CHOICES, default="HQ")
    level = models.IntegerField(default=1)

    @property
    def population(self):
        return 1

    @property
    def url(self):
        if self.type == "HQ":
            return reverse("hq", kwargs={"village_id": self.village.id})

    class Meta:
        unique_together = (("village", "type"),)
