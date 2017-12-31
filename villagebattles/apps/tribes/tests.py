from django.shortcuts import reverse
from django.test import TestCase, Client

from ..users.models import User
from ..game.models import World


class TribeTests(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")

        session = self.client.session
        session["world"] = World.objects.get().id
        session.save()

    def test_tribe_page(self):
        response = self.client.get(reverse("tribe"))
        self.assertEquals(response.status_code, 200)
