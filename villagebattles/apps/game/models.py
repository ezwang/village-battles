from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from ..users.models import User
from .constants import get_max_building_level, get_building_population, get_wood_rate, get_clay_rate, get_iron_rate, get_max_capacity, get_max_population, get_troop_population


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
        return get_max_capacity(self._building_level("WH"))

    @property
    def population(self):
        building_pop = sum([x.population for x in self.buildings.all()])
        troop_pop = sum([x.population for x in self.troops.all()])
        return building_pop + troop_pop

    @property
    def max_population(self):
        return get_max_population(self._building_level("FM"))

    def pay(self, wood, clay, iron):
        if wood > self.wood or clay > self.clay or iron > self.iron:
            return False
        self.wood -= wood
        self.clay -= clay
        self.iron -= iron
        self.save()
        return True

    def _do_resource_update(self, end_time=None):
        now = timezone.now()
        if end_time is None:
            if hasattr(self, "_done_resource_update"):
                return
            self._done_resource_update = True
        else:
            if end_time > self._update:
                now = end_time
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
        return get_wood_rate(self._building_level("WM"))

    @property
    def clay_rate(self):
        """ How much clay should be produced every hour. """
        return get_clay_rate(self._building_level("CM"))

    @property
    def iron_rate(self):
        """ How much iron should be produced every hour. """
        return get_iron_rate(self._building_level("IM"))

    def _building_level(self, type):
        try:
            return self.buildings.get(type=type).level
        except Building.DoesNotExist:
            return 0

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
        ("BR", "Barracks"),
        ("RP", "Rally Point"),
    )
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="buildings")
    type = models.CharField(max_length=2, choices=CHOICES, default="HQ")
    level = models.IntegerField(default=1)

    @property
    def max_level(self):
        return get_max_building_level(self.type)

    @property
    def level_after_upgrade(self):
        return self.level + self.village.buildqueue.filter(type=self.type).count()

    @property
    def population(self):
        return get_building_population(self.type, self.level)

    @property
    def url(self):
        if self.type == "HQ":
            return reverse("hq", kwargs={"village_id": self.village.id})
        elif self.type == "BR":
            return reverse("barracks", kwargs={"village_id": self.village.id})

    class Meta:
        unique_together = (("village", "type"),)


class BuildTask(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="buildqueue")
    type = models.CharField(max_length=2, choices=Building.CHOICES)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)

    @property
    def new_level(self):
        try:
            level = self.village.buildings.get(type=self.type).level
        except Building.DoesNotExist:
            level = 0
        level += self.village.buildqueue.filter(start_time__lt=self.start_time, type=self.type).count()
        return level + 1

    def process(self):
        build = self.village.buildings.filter(type=self.type)
        if build.exists():
            build = build.first()
            build.level += 1
            build.save()
        else:
            Building.objects.create(
                village=village,
                type=self.type,
                level=1
            )
        if self.type in ["WM", "CM", "IM", "WH"]:
            self.village._do_resource_update(self.end_time)


class Troop(models.Model):
    CHOICES = (
        ("SP", "Spearman"),
        ("SW", "Swordsman"),
        ("AX", "Axeman"),
    )
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="troops")
    type = models.CharField(max_length=2, choices=CHOICES, default="SP")
    amount = models.IntegerField()

    @property
    def population(self):
        return self.amount * get_troop_population(self.type)

    class Meta:
        unique_together = (("village", "type"),)


class TroopTask(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="troopqueue")
    type = models.CharField(max_length=2, choices=Troop.CHOICES)
    amount = models.IntegerField()
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)

    def process(self):
        try:
            item = self.village.troops.get(type=self.type)
            item.amount += self.amount
            item.save()
        except Troop.DoesNotExist:
            Troop.objects.create(
                village=self.village,
                type=self.type,
                amount=self.amount
            )
