from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import World, Village
from ..users.models import User


class ResourceTests(TestCase):
    def setUp(self):
        self.world = World.objects.create(name="World 1")
        self.user = User.objects.create_user(username="test", password="test")

    def test_auto_update(self):
        """ Make sure resource values are being updated on each call. """
        village = Village.objects.create(
            x=500,
            y=500,
            name="Test Village",
            world=self.world,
            owner=self.user
        )
        initial_wood = village._wood
        expected_wood = min(initial_wood + village.wood_rate, village.max_capacity)
        village._update = timezone.now() - timedelta(hours=1)
        village.save()
        self.assertEquals(village.wood, expected_wood, (village.wood, expected_wood))
