from math import sqrt
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from .helpers import get_new_village_coords, get_villages, calculate_travel_time
from .models import Village, World, Building, BuildTask, Troop, TroopTask, Attack
from ..users.models import User
from .constants import get_building_cost, get_building_population, get_troop_cost, get_troop_population, get_troop_travel
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
            "buildings": village.buildings.order_by("type"),
            "troops": village.troops.order_by("type"),
            "outgoing": village.outgoing.order_by("end_time"),
            "incoming": village.incoming.order_by("end_time"),
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
                    if village.population_after_upgrade + pop <= village.max_population:
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
                if village.population_after_upgrade + pop <= village.max_population:
                    if village.buildings.filter(type=type).exists() or village.buildqueue.filter(type=type).exists():
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


@login_required
def barracks(request, village_id):
    village = get_object_or_404(Village, id=village_id, owner=request.user)

    if not village.buildings.filter(type="BR").exists():
        messages.error(request, "You do not have a barracks!")
        return redirect("village", village_id=village.id)

    if request.method == "POST":
        order = []
        for choice, _ in Troop.CHOICES:
            amt = int(request.POST.get(choice, 0))
            order.append((choice, amt))
        if sum([x[1] for x in order]) == 0:
            messages.warning(request, "You did not order any troops!")
        else:
            total_wood, total_clay, total_iron = 0, 0, 0
            total_pop = 0
            for troop, amt in order:
                wood, clay, iron = get_troop_cost(troop)
                pop = get_troop_population(troop)
                total_wood += wood * amt
                total_clay += clay * amt
                total_iron += iron * amt
                total_pop += pop * amt
            if village.population_after_upgrade + total_pop <= village.max_population:
                if village.pay(total_wood, total_clay, total_iron):
                    for troop, amt in order:
                        if amt == 0:
                            continue
                        TroopTask.objects.create(
                            village=village,
                            type=troop,
                            amount=amt
                        )
                    messages.success(request, "Your troops have been queued!")
                else:
                    messages.error(request, "You do not have enough resources to create this number of troops!")
            else:
                messages.error(request, "You do not have enough farm space to create this number of troops!")
            process([village])
        return redirect("barracks", village_id=village.id)

    context = {
        "village": village,
        "troop_options": Troop.CHOICES,
        "troop_queue": village.troopqueue.order_by("start_time"),
        "troops": Troop.objects.filter(village=village).order_by("type"),
    }

    return render(request, "game/barracks.html", context)


@login_required
def rally(request, village_id):
    village = get_object_or_404(Village, id=village_id, owner=request.user)

    if not village.buildings.filter(type="RP").exists():
        messages.error(request, "You do not have a rally point!")
        return redirect("village", village_id=village.id)

    if request.method == "POST":
        x = request.POST.get("x")
        y = request.POST.get("y")

        if not x or not y:
            messages.error(request, "No coordinates entered!")
            return redirect("rally", village_id=village.id)

        try:
            x = int(x)
            y = int(y)
        except ValueError:
            messages.error(request, "Invalid coordinates!")
            return redirect("rally", village_id=village.id)

        try:
            target = Village.objects.get(x=x, y=y, world=village.world)
        except Village.DoesNotExist:
            messages.error(request, "Village does not exist!")
            return redirect("rally", village_id=village.id)

        if target.owner == request.user:
            messages.error(request, "You cannot attack your own villages!")
            return redirect("rally", village_id, village.id)

        attackers = []
        flag = False
        for troop, name in Troop.CHOICES:
            amt = int(request.POST.get(troop, 0))
            if amt > 0:
                try:
                    if village.troops.get(type=troop).amount < amt:
                        messages.error(request, "You do not have enough {}!".format(name))
                        flag = True
                        break
                except Troop.DoesNotExist:
                    messages.error(request, "You do not have any {}!".format(name))
                    flag = True
                    break
                attackers.append((troop, amt))

        if flag:
            return redirect("rally", village_id=village.id)

        attack = Attack.objects.create(
            source=village,
            destination=target,
            end_time=timezone.now() + timedelta(seconds=calculate_travel_time(village, target, [x[0] for x in attackers]))
        )

        for troop, amt in attackers:
            cur = village.troops.get(type=troop)
            cur.amount -= amt
            if cur.amount > 0:
                cur.save()
            else:
                cur.delete()
            Troop.objects.create(
                attack=attack,
                type=troop,
                amount=amt
            )

        messages.success(request, "Attack has been scheduled!")

        return redirect("village", village_id=village.id)

    context = {
        "village": village
    }

    return render(request, "game/rally.html", context)


@login_required
def map_coord(request):
    world = get_object_or_404(World, id=request.session["world"])

    x = request.GET.get("x")
    y = request.GET.get("y")

    try:
        vil = Village.objects.get(x=x, y=y, world=world)
        return JsonResponse({"exists": True, "name": vil.name, "owner": vil.owner.username})
    except Village.DoesNotExist:
        return JsonResponse({"exists": False})
