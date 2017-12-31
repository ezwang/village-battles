from .models import Quest, Village
from .helpers import get_villages


def _check_building_level(building, level):
    def func(request):
        for vil in get_villages(request):
            if vil.get_level(building) >= level:
                return True
        return False
    return func


QUESTS = {
    1: {
        "name": "First Steps",
        "body": ("Upgrade your headquarters to level 2. To do this, click on 'Headquarters' from the village screen "
                 "and then click 'Upgrade' next to the Headquarters building."),
        "reward": [200, 200, 200],
        "finished": _check_building_level("HQ", 2),
        "unlocks": [2]
    },
    2: {
        "name": "Build a Barracks",
        "body": "Upgrade your headquarters to level 3 and build a barracks. The barracks will unlock at headquarters level 3.",
        "reward": [300, 300, 300],
        "finished": _check_building_level("BR", 1),
        "unlocks": []
    }
}


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


def process_quest(request, world, quest):
    if "village" in request.session:
        current_village = Village.objects.prefetch_related("buildings").get(id=request.session["village"])
    else:
        current_village = get_villages(request).first()

    current_village.wood = current_village.wood + QUESTS[quest.type]["reward"][0]
    current_village.clay = current_village.clay + QUESTS[quest.type]["reward"][1]
    current_village.iron = current_village.iron + QUESTS[quest.type]["reward"][2]
    current_village.save()

    new_quests = QUESTS[quest.type].get("unlocks", [])
    Quest.objects.bulk_create([Quest(world=world, user=request.user, type=new_quest) for new_quest in new_quests])
