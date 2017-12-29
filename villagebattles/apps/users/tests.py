from django.test import TestCase, Client
from django.urls import reverse

from .models import User


class UnauthenticatedTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)


class BasicTests(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")
        session = self.client.session
        session["world"] = 1
        session.save()

    def test_world_creation(self):
        response = self.client.get(reverse("start"))
        self.assertRedirects(response, reverse("create_village"))

    def test_village_creation(self):
        response = self.client.post(reverse("create_village"))
        self.assertRedirects(response, reverse("village", kwargs={"village_id": 1}))
