from datetime import timedelta
from mock import patch

from django.test import TestCase
from django.utils import timezone

from .models import World, Village, Attack, TroopTask, Troop, Building
from ..users.models import User
from .tasks import process_village
from .helpers import create_default_setup
from .constants import get_troop_time, get_barracks_buff


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
        create_default_setup(self.village)
        self.village2 = Village.objects.create(
            x=501,
            y=501,
            name="Test Village 2",
            world=self.world,
            owner=self.user2
        )
        create_default_setup(self.village2)

    def test_troop_creation(self):
        """ Make sure producing troops works. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10,
            step_time=now - timedelta(days=1),
            end_time=now - timedelta(days=1)
        )
        process_village(self.village, now)
        self.assertEqual(self.village.troopqueue.count(), 0)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 10)

    def test_troop_creation_with_barracks(self):
        """ Make sure barracks increases recruitment time. """
        barracks = Building.objects.create(
            village=self.village,
            type="BR",
            level=5
        )

        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=100
        )

        expected_amount = int(1800 / int(get_troop_time(TYPE) * get_barracks_buff(barracks.level)))

        past = now - timedelta(minutes=30)
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)

        process_village(self.village, now)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, expected_amount)

    def test_troop_creation_middle(self):
        """ Make sure producing troops is the same amount with a call in the middle. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        time = get_troop_time(TYPE)
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10
        )
        # Create event
        past = now - timedelta(seconds=11 * time)
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)
        self.assertFalse(self.village.troops.filter(type=TYPE).exists())

        # Two seconds before the troop
        rightbefore = past + timedelta(seconds=time - 1)
        with patch.object(timezone, "now", return_value=rightbefore):
            process_village(self.village, rightbefore)
        self.assertFalse(self.village.troops.filter(type=TYPE).exists())
        self.assertTrue(self.village.troopqueue.first().step_time, past + timedelta(seconds=time))

        # One troop and 1 second later
        rightafter = past + timedelta(seconds=time + 1)
        with patch.object(timezone, "now", return_value=rightafter):
            process_village(self.village, rightafter)
        self.assertEqual(self.village.troopqueue.first().amount, 9)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 1)

        # Around halfway
        middle = now - timedelta(seconds=6 * time)
        with patch.object(timezone, "now", return_value=middle):
            process_village(self.village, middle)
        self.assertTrue(self.village.troops.get(type=TYPE).amount > 3)

        # Completion
        process_village(self.village, now)

        self.assertEqual(self.village.troopqueue.count(), 0)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 10)

    def test_multiple_troop_creation(self):
        """ Test multiple amounts of same troop in different orders. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10,
            step_time=now - timedelta(hours=12),
            end_time=now - timedelta(days=1)
        )
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10,
            step_time=now - timedelta(days=1),
            end_time=now - timedelta(days=2)
        )
        process_village(self.village, now)
        self.assertEqual(self.village.troopqueue.count(), 0)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 20)

    def test_partial_troop_creation(self):
        """ Make sure producing troops is incremental. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        time = get_troop_time(TYPE) * 1.5
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10,
            start_time=now - timedelta(seconds=time),
            step_time=now - timedelta(seconds=get_troop_time(TYPE)),
            end_time=now + timedelta(seconds=get_troop_time(TYPE) * 10 - time)
        )
        process_village(self.village, now)
        self.assertEqual(self.village.troopqueue.count(), 1)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 1)

    def test_troop_creation_via_autoqueue(self):
        """ Tests troop creation without manually setting a time. """
        now = timezone.now()
        past = now - timedelta(days=1)
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            village=self.village,
            type=TYPE,
            amount=10,
            start_time=past
        )
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)
        process_village(self.village, now)
        self.assertEqual(self.village.troopqueue.count(), 0)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 10)

    def test_auto_update(self):
        """ Make sure resource values are being updated on each call. """
        initial_wood = self.village._wood
        initial_clay = self.village._clay
        initial_iron = self.village._iron
        expected_wood = min(initial_wood + self.village.wood_rate, self.village.max_capacity)
        expected_clay = min(initial_clay + self.village.clay_rate, self.village.max_capacity)
        expected_iron = min(initial_iron + self.village.iron_rate, self.village.max_capacity)
        self.village._update = timezone.now() - timedelta(hours=1)
        self.village.save()
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))
        self.assertEquals(self.village.clay, expected_clay, (self.village.clay, expected_clay))
        self.assertEquals(self.village.iron, expected_iron, (self.village.iron, expected_iron))

    def test_loyalty_regeneration(self):
        past = timezone.now() - timedelta(weeks=1)
        with patch.object(timezone, "now", return_value=past):
            self.village.loyalty = 20
            self.village.save()

        self.assertEqual(self.village.loyalty, 100)

    def test_update_with_loot_first(self):
        """ Test resource update with incoming loot from an attack beforehand. """
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
        """ Test resource update with incoming loot from an attack afterwards. """
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
        """ Test resource update with incoming loot from an attack at the same time. """
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

    def test_attack(self):
        """ Test attacking and returning. """
        now = timezone.now()
        attack = Attack.objects.create(
            source=self.village,
            destination=self.village2,
            end_time=now - timedelta(hours=1)
        )
        Troop.objects.create(
            attack=attack,
            type="SP",
            amount=3
        )
        process_village(self.village, now)
        self.assertEquals(Attack.objects.count(), 0)
        self.assertTrue(self.village.troops.get(type="SP").amount, 3)
