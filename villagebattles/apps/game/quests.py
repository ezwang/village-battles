from .models import Quest, Village, World
from .helpers import get_villages


def _check_building_level(building, level):
    def func(request):
        for vil in get_villages(request):
            if vil.get_level(building) >= level:
                return True
        return False
    return func


def _check_troops(troop, amount):
    def func(request):
        for vil in get_villages(request):
            troops = vil.troops.filter(type=troop).first()
            if not troops:
                continue
            if troops.amount >= amount:
                return True
        return False
    return func


def _check_profile(request):
    return bool(request.user.profile)


def _check_tribe(request):
    if "world" in request.session:
        world = World.objects.get(id=request.session["world"])
        return request.user.tribes.filter(world=world).exists()
    else:
        return False


QUESTS = {
    1: {
        "name": "First Steps",
        "body": ("Upgrade your headquarters to level 2. To do this, click on 'Headquarters' from the village screen "
                 "and then click 'Upgrade' next to the Headquarters building. After you have done so, wait for the build ",
                 "to finish and come back to this page to get your reward."),
        "reward": [200, 200, 200],
        "finished": _check_building_level("HQ", 2),
        "unlocks": [2, 3]
    },
    2: {
        "name": "Build a Barracks",
        "body": "Upgrade your headquarters to level 3 and build a barracks. The barracks will unlock at headquarters level 3.",
        "reward": [300, 300, 300],
        "finished": _check_building_level("BR", 1),
        "unlocks": [4, 6, 7]
    },
    3: {
        "name": "A Little Bit About Yourself",
        "body": ("Change your profile text. You can do this by going to 'Settings' in the upper right. There is a form "
                 "on the left of the screen that you can use to change your profile."),
        "reward": [100, 100, 100],
        "finished": _check_profile,
        "unlocks": [5]
    },
    4: {
        "name": "Creating an Army",
        "body": ("Create 10 spearmen. You can do this by clicking on 'Barracks' from the village screen. "
                 "You will be able to use the form on the barracks page to create new troops."),
        "reward": [500, 500, 500],
        "finished": _check_troops("SP", 10),
        "unlocks": [8]
    },
    5: {
        "name": "Forming Alliances",
        "body": "Create or join a tribe. You can do this by clicking on 'Tribe' at the top of the page.",
        "reward": [100, 100, 100],
        "finished": _check_tribe,
        "unlocks": []
    },
    6: {
        "name": "Building Defenses",
        "body": "You need strong defenses to protect against an attack. Build a wall.",
        "reward": [100, 100, 100],
        "finished": _check_building_level("WA", 1),
        "unlocks": [8]
    },
    7: {
        "name": "Increasing Storage Space",
        "body": ("If you want to store more resources, you need to upgrade your warehouse. "
                 "Upgrade your warehouse to level 2."),
        "reward": [100, 100, 100],
        "finished": _check_building_level("WH", 2),
        "unlocks": []
    },
    8: {
        "name": "Scouting the Enemy, Part 1",
        "body": ("You will need to make a stable in order to create more types of troops."
                 "Build a stable. This requires a level 10 headquarters."),
        "reward": [1000, 1000, 1000],
        "finished": _check_building_level("ST", 1),
        "unlocks": [9]
    },
    9: {
        "name": "Scouting the Enemy, Part 2",
        "body": "Use your new stable to build 5 scouts.",
        "reward": [500, 500, 500],
        "finished": _check_troops("SC", 5),
        "unlocks": []
    }
}


def get_all_quests():
    return list(QUESTS.keys())


def get_quests(world, user):
    return Quest.objects.filter(world=world, user=user)


def get_quest_name(quest):
    return QUESTS[quest]["name"]


def get_quest_description(quest):
    return QUESTS[quest]["body"]


def get_quest_reward(quest):
    return QUESTS[quest]["reward"]


def get_quest_finished(quest, request):
    return QUESTS[quest]["finished"](request)


def get_linked_quests(quest):
    return QUESTS[quest].get("unlocks", [])


def process_quest(request, world, quest):
    if "village" in request.session:
        current_village = Village.objects.prefetch_related("buildings").get(id=request.session["village"])
    else:
        current_village = get_villages(request).first()

    current_village.wood = current_village.wood + QUESTS[quest.type]["reward"][0]
    current_village.clay = current_village.clay + QUESTS[quest.type]["reward"][1]
    current_village.iron = current_village.iron + QUESTS[quest.type]["reward"][2]
    current_village.save()

    new_quests = get_linked_quests(quest.type)
    for new_quest in new_quests:
        Quest.objects.get_or_create(world=world, user=request.user, type=new_quest)
