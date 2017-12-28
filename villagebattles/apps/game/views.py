from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .helpers import get_new_village_coords, get_villages
from .models import Village, World, Building, BuildTask, Troop
from ..users.models import User
from .constants import get_building_cost, get_building_population
from .tasks import process


@login_required
def create_village(request):
    if get_villages(request).count() > 0:
        return redirect("dashboard")
    world = get_object_or_404(World, id=request.session["world"])
    if request.method == "POST":
        x, y = get_new_village_coords(world)
        vil = Village.objects.create(
            x=x,
            y=y,
            name="{}'s Village".format(request.user.username),
            owner=request.user,
            world=world
        )
        for t in ["HQ", "WM", "IM", "CM", "WH", "FM", "RP"]:
            Building.objects.create(
                village=vil,
                type=t,
                level=1
            )
        messages.success(request, "Your new village has been created!")
        return redirect("village", village_id=vil.id)

    return render(request, "game/create_village.html")


@login_required
def dashboard(request):
    if get_villages(request).count() == 0:
        return redirect("create_village")

    context = {
        "villages": get_villages(request)
    }

    return render(request, "game/dashboard.html", context)


@login_required
def village(request, village_id):
    village = get_object_or_404(Village, id=village_id)
    if request.user == village.owner:
        context = {
            "village": village,
            "buildings": Building.objects.filter(village=village).order_by("type")
        }

        request.session["village"] = village.id

        return render(request, "game/village.html", context)
    else:
        return render(request, "game/village_info.html", {"village": village})


@login_required
def map(request):
    vil = get_villages(request).first()

    context = {
        "x": vil.x,
        "y": vil.y
    }

    return render(request, "game/map.html", context)


@login_required
def map_load(request):
    world = get_object_or_404(World, id=request.session["world"])
    output = []
    for vil in Village.objects.filter(world=world):
        output.append({
            "id": vil.id,
            "x": vil.x,
            "y": vil.y,
            "name": vil.name,
            "owner": {
                "id": vil.owner.id,
                "name": vil.owner.username
            }
        })

    return JsonResponse({"villages": output})


@login_required
def user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    context = {
        "user": user,
        "villages": get_villages(request, user=user).order_by("name")
    }
    return render(request, "game/user_info.html", context)


def queue_building(village, building_type):
    BuildTask.objects.create(
        village=village,
        type=building_type
    )


@login_required
def hq(request, village_id):
    village = get_object_or_404(Village, id=village_id, owner=request.user)

    if request.method == "POST":
        if "name" in request.POST:
            name = request.POST.get("name")
            if len(name) > 3:
                village.name = name
                village.save()
                messages.success(request, "Village name has been changed!")
            else:
                messages.error(request, "Village name is too short!")
        elif "building" in request.POST:
            try:
                building = Building.objects.get(id=request.POST.get("building"), village=village)
                if building.level_after_upgrade < building.max_level:
                    cost = get_building_cost(building.type, building.level_after_upgrade)
                    pop = get_building_population(building.type, building.level) - get_building_population(building.type, building.level - 1)
                    if village.population + pop <= village.max_population:
                        if village.pay(*cost):
                            queue_building(village, building.type)
                            messages.success(request, "Building has been queued!")
                        else:
                            messages.error(request, "You do not have enough resources to create this building!")
                    else:
                        messages.error(request, "You do not have enough people to make this building!")
                else:
                    messages.error(request, "This building is already at max level!")
            except Building.DoesNotExist:
                messages.error(request, "The building you are trying to upgrade does not exist yet!")
        elif "build" in request.POST:
            type = request.POST.get("build")
            if type in [x[0] for x in Building.CHOICES]:
                cost = get_building_cost(type, 0)
                pop = get_building_population(type, 0)
                if village.population + pop <= village.max_population:
                    if village.buildings.filter(type=type).count() > 0:
                        messages.error(request, "You already have this building!")
                    else:
                        if village.pay(*cost):
                            queue_building(village, type)
                            messages.success(request, "Building has been queued!")
                        else:
                            messages.error(request, "You do not have enough resources to create this building!")
                else:
                    messages.error(request, "You do not have enough people to make this building!")
            else:
                messages.error(request, "Invalid building type passed to server!")
            pass
        process([village])
        return redirect("hq", village_id=village.id)

    built = set(Building.objects.filter(village=village).values_list("type", flat=True))

    not_built = []

    for building in Building.CHOICES:
        if building[0] not in built:
            not_built.append(building)

    context = {
        "village": village,
        "buildings": Building.objects.filter(village=village).order_by("type"),
        "troops": Troop.objects.filter(village=village).order_by("type"),
        "not_built": not_built,
        "queue": BuildTask.objects.filter(village=village)
    }

    return render(request, "game/hq.html", context)
