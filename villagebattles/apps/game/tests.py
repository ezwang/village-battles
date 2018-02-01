from datetime import timedelta
from mock import patch

from django.test import TestCase
from django.utils import timezone
from django.shortcuts import reverse

from .models import World, Village, Attack, TroopTask, Troop, Building, BuildTask
from ..users.models import User
from .tasks import process_village
from .helpers import create_default_setup, create_npc_village
from .constants import get_troop_time, get_recruitment_buff

from ..game.quests import get_all_quests, get_quest_finished, get_linked_quests
from ..users.tests import BaseTestCase


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
        for v in [self.village, self.village2]:
            Building.objects.create(
                village=v,
                type="BR",
                level=1
            )

    def test_npc_village_generation(self):
        """ Make sure the npc village generation function works. """
        village = create_npc_village(self.world)

        self.assertTrue(village)
        self.assertTrue(village.buildings.count() > 1)
        self.assertEquals(self.world.villages.count(), 3)

    def test_multiple_npc_villages(self):
        """ Make sure multiple npc villages can be generated without problems. """
        for _ in range(15):
            create_npc_village(self.world)

        self.assertEquals(self.world.villages.count(), 17)

    def test_building_upgrade(self):
        """ Test filling up the build queue and making sure all tasks are processed. """
        now = timezone.now()
        past = now - timedelta(weeks=10)
        for _ in range(10):
            BuildTask.objects.create(
                village=self.village,
                type="HQ",
                start_time=past
            )
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)
        process_village(self.village, now)
        self.assertEquals(self.village.buildqueue.count(), 0)
        self.assertEquals(self.village.get_level("HQ"), 11)

    def test_troop_creation(self):
        """ Make sure producing troops works. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            building=self.village.buildings.get(type="BR"),
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
        barracks = self.village.buildings.get(type="BR")
        barracks.level = 5
        barracks.save()

        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            building=self.village.buildings.get(type="BR"),
            type=TYPE,
            amount=100
        )

        production_speed = int(get_troop_time(TYPE) * get_recruitment_buff("BR", barracks.level))

        if production_speed > 0:
            expected_amount = min(100, int(1800 / production_speed))
        else:
            expected_amount = 100

        past = now - timedelta(minutes=30)
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)

        process_village(self.village, now)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, expected_amount)

    def test_troop_creation_middle(self):
        """ Make sure producing troops is the same amount with a call in the middle. """
        now = timezone.now()
        barracks = self.village.buildings.get(type="BR")
        TYPE = Troop.CHOICES[0][0]
        time = get_troop_time(TYPE) * get_recruitment_buff("BR", barracks.level)
        TroopTask.objects.create(
            building=barracks,
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

    def test_troop_creation_during_upgrade(self):
        """ Test troop creation in the middle of a barracks upgrade. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        time = get_troop_time(TYPE)
        TroopTask.objects.create(
            building=self.village.buildings.get(type="BR"),
            type=TYPE,
            amount=10
        )
        BuildTask.objects.create(
            village=self.village,
            type="BR",
            end_time=now - timedelta(seconds=6 * time)
        )
        past = now - timedelta(seconds=11 * time)
        with patch.object(timezone, "now", return_value=past):
            process_village(self.village, past)

        middle = now - timedelta(seconds=6 * time)
        with patch.object(timezone, "now", return_value=middle):
            process_village(self.village, middle)

        process_village(self.village, now)

        self.assertEqual(self.village.get_level("BR"), 2)
        self.assertEqual(self.village.troops.get(type=TYPE).amount, 10)

    def test_multiple_troop_creation(self):
        """ Test multiple amounts of same troop in different orders. """
        now = timezone.now()
        TYPE = Troop.CHOICES[0][0]
        TroopTask.objects.create(
            building=self.village.buildings.get(type="BR"),
            type=TYPE,
            amount=10,
            step_time=now - timedelta(hours=12),
            end_time=now - timedelta(days=1)
        )
        TroopTask.objects.create(
            building=self.village.buildings.get(type="BR"),
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
            building=self.village.buildings.get(type="BR"),
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
            building=self.village.buildings.get(type="BR"),
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
            self.village._update = past
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
            source=self.village2,
            destination=self.village,
            loot="100,100,100",
            end_time=now - timedelta(minutes=30),
            type=Attack.RETURN
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
            source=self.village2,
            destination=self.village,
            loot="100,100,100",
            end_time=now - timedelta(hours=2),
            type=Attack.RETURN
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
            source=self.village2,
            destination=self.village,
            loot="100,100,100",
            end_time=now - timedelta(hours=1),
            type=Attack.RETURN
        )
        process_village(self.village, now)
        self.assertEquals(self.village.wood, expected_wood, (self.village.wood, expected_wood))

    def test_attack(self):
        """ Test attacking and returning. """
        now = timezone.now()
        attack = Attack.objects.create(
            source=self.village,
            destination=self.village2,
            end_time=now - timedelta(hours=1),
            type=Attack.ATTACK
        )
        Troop.objects.create(
            attack=attack,
            type="SP",
            amount=3
        )
        process_village(self.village, now)
        self.assertEquals(Attack.objects.count(), 0)
        self.assertTrue(self.village.owner.reports.count(), 1)
        self.assertTrue(self.village2.owner.reports.count(), 1)
        self.assertTrue(self.village.troops.get(type="SP").amount, 3)

    def test_attack_catapult(self):
        """ Test attacking with catapults. """
        now = timezone.now()
        attack = Attack.objects.create(
            source=self.village,
            destination=self.village2,
            end_time=now - timedelta(hours=1),
            type=Attack.ATTACK,
            loot="RP"
        )
        Troop.objects.create(
            attack=attack,
            type="CA",
            amount=100
        )
        self.assertEquals(self.village2.buildings.get(type="RP").level, 1)
        process_village(self.village, now)
        self.assertFalse(self.village2.buildings.filter(type="RP").exists())

    def test_attack_npc_village(self):
        """ Test attacking a NPC village. """
        village = create_npc_village(self.world)
        now = timezone.now()
        attack = Attack.objects.create(
            source=self.village,
            destination=village,
            end_time=now - timedelta(hours=3),
            type=Attack.ATTACK
        )
        Troop.objects.create(
            attack=attack,
            type="SP",
            amount=10
        )
        process_village(self.village, now)
        self.assertEquals(Attack.objects.count(), 0)
        self.assertTrue(self.village.owner.reports.count(), 1)

    def test_attack_with_noble(self):
        """ Test attacking with noble decreases loyalty. """
        now = timezone.now()
        attack = Attack.objects.create(
            source=self.village,
            destination=self.village2,
            end_time=now - timedelta(hours=1),
            type=Attack.ATTACK
        )
        Troop.objects.create(
            attack=attack,
            type="SP",
            amount=100
        )
        Troop.objects.create(
            attack=attack,
            type="NB",
            amount=1
        )
        process_village(self.village, now)
        self.assertTrue(self.village.loyalty, 100)
        self.assertTrue(self.village2.loyalty < 100, self.village2.loyalty)

    def test_support(self):
        """ Test supporting another player. """
        now = timezone.now()
        support = Attack.objects.create(
            source=self.village,
            destination=self.village2,
            end_time=now - timedelta(hours=1),
            type=Attack.SUPPORT
        )
        Troop.objects.create(
            attack=support,
            type="SP",
            amount=100
        )
        process_village(self.village, now)
        self.assertEqual(self.village2.troops.count(), 0)
        self.assertEqual(self.village2.all_troops.count(), 1)
        self.assertEqual(self.village2.foreign_troops.count(), 1)
        self.assertEqual(self.village.external_troops.count(), 1)


class QuestTests(BaseTestCase):
    def test_quest_finished(self):
        """ Make sure that all quests are currently unfinished. """
        village = self.do_enter_game()

        response = self.client.get(reverse("village", kwargs={"village_id": village.id}))
        self.assertEqual(response.status_code, 200)

        request = response.wsgi_request

        for quest in get_all_quests():
            self.assertFalse(get_quest_finished(quest, request))

    def test_finish_quest(self):
        """ Make sure that the quests finish correctly. """
        village = self.do_enter_game()

        hq = village.buildings.get(type="HQ")
        hq.level = 5
        hq.save()

        response = self.client.post(reverse("submit_quest"), {"id": 1})
        self.assertRedirects(response, reverse("village", kwargs={"village_id": village.id}))

        self.assertFalse(self.user.quests.filter(world=village.world, type=1).exists())
        self.assertTrue(self.user.quests.filter(world=village.world).exists())

    def test_all_quests_reachable(self):
        """ Make sure all quests are reachable from the initial quest. """
        expected = set(get_all_quests())
        actual = set([1])
        queue = [1]
        while queue:
            item = queue.pop()
            linked = get_linked_quests(item)
            for link in linked:
                if link not in actual:
                    actual.add(link)
                    queue.append(link)
        self.assertEquals(actual, expected)
