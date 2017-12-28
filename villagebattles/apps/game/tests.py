from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import World, Village, Attack
from ..users.models import User
from .tasks import process_village


class ResourceTests(TestCase):
    def setUp(self):
        self.world = World.objects.create(name="World 1")
        self.user = User.objects.create_user(username="test", password="test")
        self.user2 = User.objects.create_user(username="test2", password="test")
        self.village = Village.objects.create(
            x=500,
            y=500,
            name="Test Village",
            world=self.world,
            owner=self.user
        )
        self.village2 = Village.objects.create(
            x=501,
            y=501,
            name="Test Village 2",
            world=self.world,
            owner=self.user2
        )

    def test_auto_update(self):
        """ Make sure resource values are being updated on each call. """
        initial_wood = self.village._wood
        expected_wood = min(initial_wood + self.village.wood_rate, self.village.max_capacity)
        self.village._update = timezone.now() - timedelta(hours=1)
        self.village.save()
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))

    def test_update_with_loot_first(self):
        now = timezone.now()
        initial_wood = self.village._wood
        expected_wood = min(initial_wood + self.village.wood_rate + 100, self.village.max_capacity)
        self.village._update = now - timedelta(hours=1)
        self.village.save()
        Attack.objects.create(
            source=self.village,
            destination=self.village2,
            loot="100,100,100",
            end_time=now - timedelta(minutes=30),
            returning=True
        )
        process_village(self.village, now)
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))

    def test_update_with_loot_last(self):
        now = timezone.now()
        initial_wood = self.village._wood
        expected_wood = min(initial_wood + self.village.wood_rate + 100, self.village.max_capacity)
        self.village._update = now - timedelta(hours=1)
        self.village.save()
        Attack.objects.create(
            source=self.village,
            destination=self.village2,
            loot="100,100,100",
            end_time=now - timedelta(hours=2),
            returning=True
        )
        process_village(self.village, now)
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))

    def test_update_with_loot_same_time(self):
        now = timezone.now()
        initial_wood = self.village._wood
        expected_wood = min(initial_wood + self.village.wood_rate + 100, self.village.max_capacity)
        self.village._update = now - timedelta(hours=1)
        self.village.save()
        Attack.objects.create(
            source=self.village,
            destination=self.village2,
            loot="100,100,100",
            end_time=now - timedelta(hours=1),
            returning=True
        )
        process_village(self.village, now)
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))
