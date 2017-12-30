from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from mock import patch
from datetime import timedelta

from .models import User
from ..game.models import Village, World, Building


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
        session["world"] = World.objects.get().id
        session.save()

    def test_world_creation(self):
        response = self.client.get(reverse("start"))
        self.assertRedirects(response, reverse("create_village"))

    def test_common_pages(self):
        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("settings"))
        self.assertEqual(response.status_code, 200)

    def do_enter_game(self):
        response = self.client.post(reverse("create_village"))
        self.assertEqual(Village.objects.all().count(), 1)

        village_id = Village.objects.get().id
        self.assertRedirects(response, reverse("village", kwargs={"village_id": village_id}))

        return Village.objects.get(id=village_id)

    def test_village_creation(self):
        """ Make sure that creating villages works. """
        village = self.do_enter_game()

        response = self.client.get(reverse("hq", kwargs={"village_id": village.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("rally", kwargs={"village_id": village.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("barracks", kwargs={"village_id": village.id}))
        self.assertRedirects(response, reverse("village", kwargs={"village_id": village.id}))

    def do_build(self, village, building):
        old_count = village.buildqueue.count()
        try:
            data = {"building": village.buildings.get(type=building).id}
        except Building.DoesNotExist:
            data = {"build": building}
        response = self.client.post(reverse("hq", kwargs={"village_id": village.id}), data)
        self.assertRedirects(response, reverse("hq", kwargs={"village_id": village.id}))
        self.assertEquals(village.buildqueue.count(), old_count + 1)

    def test_building_upgrade(self):
        """ Make sure that upgrading buildings works. """
        village = self.do_enter_game()
        now = timezone.now()

        with patch.object(timezone, "now", return_value=now - timedelta(days=1)):
            village._update = timezone.now()
            village.save()

            self.do_build(village, "HQ")

        response = self.client.get(reverse("hq", kwargs={"village_id": village.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEquals(village.buildings.get(type="HQ").level, 2)

    def test_troop_creation(self):
        """ Make sure that making troops works. """
        village = self.do_enter_game()
        now = timezone.now()

        Building.objects.create(
            village=village,
            type="BR",
            level=5,
        )

        with patch.object(timezone, "now", return_value=now - timedelta(days=1)):
            village._update = timezone.now()
            village.save()

            response = self.client.post(reverse("barracks", kwargs={"village_id": village.id}), {"SP": 10})
            self.assertRedirects(response, reverse("barracks", kwargs={"village_id": village.id}))

        response = self.client.get(reverse("hq", kwargs={"village_id": village.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEquals(village.troops.get(type="SP").amount, 10)
