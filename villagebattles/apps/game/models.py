from decimal import Decimal
from datetime import timedelta
from math import ceil

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from ..users.models import User
from .battle import process_attack
from .constants import (get_max_building_level, get_building_population, get_wood_rate, get_clay_rate, get_iron_rate,
                        get_max_capacity, get_max_population, get_troop_population, get_troop_time, get_recruitment_buff,
                        get_loyalty_regen)


class World(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Village(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    name = models.TextField()
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="villages")
    _loyalty = models.DecimalField(max_digits=9, decimal_places=6, default=100)

    _wood = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)
    _clay = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)
    _iron = models.DecimalField(max_digits=16, decimal_places=6, default=settings.STARTING_RESOURCES)

    _update = models.DateTimeField(default=timezone.now)

    @property
    def max_capacity(self):
        return get_max_capacity(self.get_level("WH"))

    @property
    def troopqueue(self):
        return TroopTask.objects.filter(building__village=self)

    def get_level(self, building):
        try:
            return self.buildings.get(type=building).level
        except Building.DoesNotExist:
            return 0

    @property
    def troop_population(self):
        in_village = sum([x.population for x in self.troops.all()])
        attacking = sum([x.population for x in self.outgoing.all()])
        return in_village + attacking

    @property
    def population(self):
        troop_pop = self.troop_population
        building_pop = sum([x.population for x in self.buildings.all()])
        return building_pop + troop_pop

    @property
    def population_after_upgrade(self):
        troop_pop = self.troop_population
        building_queue = sum([x.population_after_upgrade for x in self.buildings.all()])
        troop_queue = sum([x.population for x in self.troopqueue.all()])
        return troop_pop + building_queue + troop_queue

    @property
    def max_population(self):
        return get_max_population(self.get_level("FM"))

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
        self.refresh_from_db()
        diff = (now - self._update)
        diff = int(diff.total_seconds()) + (diff.microseconds / Decimal(1000000))
        self.wood = self._wood + (diff / Decimal(3600)) * self.wood_rate
        self.clay = self._clay + (diff / Decimal(3600)) * self.clay_rate
        self.iron = self._iron + (diff / Decimal(3600)) * self.iron_rate
        self.loyalty = self._loyalty + (diff / Decimal(3600)) * get_loyalty_regen()
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
        return get_wood_rate(self.get_level("WM"))

    @property
    def clay_rate(self):
        """ How much clay should be produced every hour. """
        return get_clay_rate(self.get_level("CM"))

    @property
    def iron_rate(self):
        """ How much iron should be produced every hour. """
        return get_iron_rate(self.get_level("IM"))

    @property
    def loyalty(self):
        self._do_resource_update()
        return int(self._loyalty)

    @loyalty.setter
    def loyalty(self, x):
        self._loyalty = min(max(0, x), 100)

    @wood.setter
    def wood(self, x):
        self._wood = min(x, self.max_capacity)

    @clay.setter
    def clay(self, x):
        self._clay = min(x, self.max_capacity)

    @iron.setter
    def iron(self, x):
        self._iron = min(x, self.max_capacity)

    @property
    def url(self):
        return reverse("village", kwargs={"village_id": self.id})

    @property
    def troops(self):
        return self.all_troops.filter(original__isnull=True).order_by("type")

    @property
    def foreign_troops(self):
        return self.all_troops.filter(original__isnull=False).order_by("type")

    def __str__(self):
        return "{} ({}|{})".format(self.name, self.x, self.y)

    class Meta:
        unique_together = (("x", "y", "world"),)


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
        ("ST", "Stable"),
        ("WS", "Workshop"),
        ("AC", "Academy"),
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
    def population_after_upgrade(self):
        return get_building_population(self.type, self.level_after_upgrade)

    @property
    def url(self):
        if self.type == "HQ":
            return reverse("hq", kwargs={"village_id": self.village.id})
        elif self.type == "BR":
            return reverse("barracks", kwargs={"village_id": self.village.id})
        elif self.type == "RP":
            return reverse("rally", kwargs={"village_id": self.village.id})
        elif self.type == "ST":
            return reverse("stable", kwargs={"village_id": self.village.id})
        elif self.type == "WS":
            return reverse("workshop", kwargs={"village_id": self.village.id})
        elif self.type == "AC":
            return reverse("academy", kwargs={"village_id": self.village.id})

    class Meta:
        unique_together = (("village", "type"),)


class BuildTask(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="buildqueue")
    type = models.CharField(max_length=2, choices=Building.CHOICES)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)

    @property
    def new_level(self):
        level = self.village.get_level(self.type)
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
                village=self.village,
                type=self.type,
                level=1
            )
        if self.type in ["WM", "CM", "IM", "WH"]:
            self.village._do_resource_update(self.end_time)
        return True


class Troop(models.Model):
    CHOICES = (
        ("SP", "Spearman"),
        ("SW", "Swordsman"),
        ("AX", "Axeman"),
        ("AR", "Archer"),
        ("SC", "Scout"),
        ("NB", "Noble"),
    )
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="all_troops", null=True)
    original = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="external_troops", null=True)
    attack = models.ForeignKey("Attack", on_delete=models.CASCADE, related_name="troops", null=True)
    type = models.CharField(max_length=2, choices=CHOICES, default="SP")
    amount = models.IntegerField()

    @property
    def population(self):
        return self.amount * get_troop_population(self.type)

    def __str__(self):
        return "<Troop: {} ({})>".format(self.get_type_display(), self.amount)

    class Meta:
        unique_together = (("village", "type", "original"),)
        ordering = ["type"]


class TroopTask(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="troopqueue")
    type = models.CharField(max_length=2, choices=Troop.CHOICES)
    amount = models.IntegerField()
    start_time = models.DateTimeField(default=timezone.now)
    step_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    @property
    def population(self):
        return self.amount * get_troop_population(self.type)

    def __str__(self):
        return "<TroopTask: {} ({})>".format(self.get_type_display(), self.amount)

    def process(self):
        now = timezone.now()
        if self.end_time <= now:
            amt = self.amount
            ret = True
        else:
            time_per_unit = int(get_troop_time(self.type) * get_recruitment_buff(self.building.type, self.building.level))
            total_time = (self.end_time - self.start_time).total_seconds()
            elapsed_time = (now - self.start_time).total_seconds()
            remaining = ceil((total_time - elapsed_time) / time_per_unit)
            amt = self.amount - remaining
            self.amount -= amt
            self.step_time = self.step_time + timedelta(seconds=amt * time_per_unit)
            self.save()
            ret = False
        try:
            item = self.building.village.troops.get(type=self.type)
            item.amount += amt
            item.save()
        except Troop.DoesNotExist:
            Troop.objects.create(
                village=self.building.village,
                type=self.type,
                amount=amt
            )
        return ret


class Attack(models.Model):
    ATTACK = "AT"
    RETURN = "RT"
    SUPPORT = "SP"

    CHOICES = (
        (ATTACK, "Attack"),
        (RETURN, "Return"),
        (SUPPORT, "Support"),
    )

    source = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="outgoing")
    destination = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="incoming")
    loot = models.TextField(null=True)
    end_time = models.DateTimeField()
    type = models.CharField(max_length=2, choices=CHOICES)

    @property
    def population(self):
        return sum([x.population for x in self.troops.all()])

    def process(self):
        from .helpers import calculate_travel_time

        if self.destination._update < self.end_time:
            self.destination._do_resource_update(self.end_time)

        if self.type == Attack.ATTACK:
            process_attack(self)
            if self.troops.count() > 0:
                # Set return journey
                self.type = Attack.RETURN

                # Swap source and destination
                temp = self.destination
                self.destination = self.source
                self.source = temp

                travel_time = calculate_travel_time(self.source, self.destination, [x.type for x in self.troops.all()])
                self.end_time = self.end_time + timedelta(seconds=travel_time)
                self.save()
                return False
            else:
                return True
        elif self.type == Attack.RETURN:
            if self.loot is not None:
                wood, clay, iron = [int(x) for x in self.loot.split(",")]
                recipient = self.destination
                recipient.wood = recipient.wood + wood
                recipient.clay = recipient.clay + clay
                recipient.iron = recipient.iron + iron
                recipient.save()
            for troop in self.troops.all():
                if self.destination.troops.filter(type=troop.type).exists():
                    existing = self.destination.troops.get(type=troop.type)
                    existing.amount += troop.amount
                    existing.save()
                else:
                    troop.village = self.destination
                    troop.attack = None
                    troop.save()
            return True
        elif self.type == Attack.SUPPORT:
            for troop in self.troops.all():
                if self.destination.all_troops.filter(original=self.source, type=troop.type).exists():
                    existing = self.destination.all_troops.get(original=self.source, type=troop.type)
                    existing.amount += troop.amount
                    existing.save()
                else:
                    troop.village = self.destination
                    troop.original = self.source
                    troop.attack = None
                    troop.save()
            return True
        else:
            raise ValueError("'{}' is not a valid action!".format(self.type))


class Report(models.Model):
    title = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    body = models.TextField()

    def __str__(self):
        return self.title
