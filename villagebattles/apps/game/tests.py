from django.test import TestCase

from .models import World, Village
from ..users.models import User


class ResourceTests(TestCase):
    def setUp(self):
        self.world = World.objects.create(name="World 1")
        self.user = User.objects.create_user(username="test", password="test")

    def test_rate_correct(self):
        village = Village.objects.create(
            x=500,
            y=500,
            name="Test Village",
            world=self.world,
            user=self.user
        )
