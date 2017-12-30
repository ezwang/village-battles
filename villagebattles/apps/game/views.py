from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator, InvalidPage
from django.db.models import F

from .helpers import get_new_village_coords, get_villages, calculate_travel_time, create_default_setup, get_troop_type_display
from .models import Village, World, Building, BuildTask, Troop, TroopTask, Attack, Report
from ..users.models import User
from .constants import (get_building_cost, get_building_population, get_troop_cost, get_troop_population,
                        building_requirements_met, get_allowed_troops)
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
        create_default_setup(vil)
        messages.success(request, "Your new village has been created!")
        return redirect("village", village_id=vil.id)

    return render(request, "game/create_village.html")


@login_required
def start(request):
    num_villages = get_villages(request).count()
    if num_villages == 0:
        return redirect("create_village")
    if num_villages == 1:
        return redirect("village", village_id=get_villages(request).first().id)
    return redirect("dashboard")


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
            "outgoing": village.outgoing.order_by("end_time"),
            "incoming": village.incoming.order_by("end_time"),
            "build_queue": village.buildqueue.all().order_by(F("end_time").asc(nulls_last=True), "start_time"),
            "troop_queue": village.troopqueue.all().order_by(F("end_time").asc(nulls_last=True), "start_time"),
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
            } if vil.owner else None
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
                if not building_requirements_met(building.type, village):
                    messages.error(request, "You no longer have the requirements to upgrade this building!")
                elif building.level_after_upgrade < building.max_level:
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
                if not building_requirements_met(type, village):
                    messages.error(request, "You do not have the requirements for this building yet.")
                elif village.population_after_upgrade + pop <= village.max_population:
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
            not_built.append((building[0], building[1], building_requirements_met(building[0], village)))

    not_built.sort(key=lambda x: (not x[2], x[0]))

    context = {
        "village": village,
        "buildings": village.buildings.all().order_by("type"),
        "troops": village.troops.all().order_by("type"),
        "not_built": not_built,
        "build_queue": village.buildqueue.all().order_by(F("end_time").asc(nulls_last=True), "start_time")
    }

    return render(request, "game/hq.html", context)


@login_required
def barracks(request, village_id):
    return troop_building(request, village_id, "BR")


@login_required
def academy(request, village_id):
    return troop_building(request, village_id, "AC")


@login_required
def stable(request, village_id):
    return troop_building(request, village_id, "ST")


@login_required
def workshop(request, village_id):
    return troop_building(request, village_id, "WS")


def troop_building(request, village_id, building_type):
    village = get_object_or_404(Village, id=village_id, owner=request.user)

    if not village.buildings.filter(type=building_type).exists():
        messages.error(request, "You do not have this building!")
        return redirect("village", village_id=village.id)

    building = village.buildings.get(type=building_type)
    building_name = building.get_type_display()
    building_choices = get_allowed_troops(building_type)

    if building_type == "BR":
        building_choices = ["SP", "SW", "AX", "AR"]
    elif building_type == "ST":
        building_choices = ["SC"]
    elif building_type == "WS":
        building_choices = []
    elif building_type == "AC":
        building_choices = ["NB"]

    if request.method == "POST":
        order = []
        for choice in building_choices:
            try:
                amt = int(request.POST.get(choice, 0))
                order.append((choice, amt))
            except ValueError:
                pass
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
                            building=building,
                            type=troop,
                            amount=amt
                        )
                    messages.success(request, "Your troops have been queued!")
                else:
                    messages.error(request, "You do not have enough resources to create this number of troops!")
            else:
                messages.error(request, "You do not have enough farm space to create this number of troops!")
            process([village])
        return redirect(building.url)

    context = {
        "village": village,
        "troop_options": [(x, get_troop_type_display(x)) for x in building_choices],
        "troop_queue": village.troopqueue.order_by(F("end_time").asc(nulls_last=True), "start_time"),
        "building_name": building_name,
    }

    return render(request, "game/barracks.html", context)


@login_required
def rally(request, village_id):
    village = get_object_or_404(Village, id=village_id, owner=request.user)

    if not village.buildings.filter(type="RP").exists():
        messages.error(request, "You do not have a rally point!")
        return redirect("village", village_id=village.id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action in ["withdrawl", "sendback"]:
            other = get_object_or_404(Village, id=request.POST.get("id"))
            if action == "withdrawl":
                troops = other.foreign_troops.filter(original=village)
                source = other
                destination = village
            else:
                troops = village.foreign_troops.filter(original=other)
                source = village
                destination = other
            if not troops.count():
                messages.error(request, "There are no troops to {}!".format(action if action == "withdrawl" else "send back"))
            else:
                travel = Attack.objects.create(
                    source=source,
                    destination=destination,
                    end_time=timezone.now() + timedelta(seconds=calculate_travel_time(source, destination, troops.values_list("type", flat=True))),
                    type=Attack.RETURN,
                )
                troops.update(village=None, original=None, attack=travel)
                messages.success(request, "Troops have been {}!".format("withdrawn" if action == "withdrawl" else "sent back"))
            return redirect("rally", village_id=village.id)

        x = request.POST.get("x")
        y = request.POST.get("y")

        if not action or action not in ["support", "attack"]:
            messages.error(request, "Invalid action specified!")
            return redirect("rally", village_id=village.id)

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

        if action == "attack" and target.owner == request.user:
            messages.error(request, "You cannot attack your own villages!")
            return redirect("rally", village_id=village.id)

        attackers = []
        flag = False
        for troop, name in Troop.CHOICES:
            try:
                amt = int(request.POST.get(troop, 0))
            except ValueError:
                messages.error(request, "Invalid troop amount for {}!".format(name))
                amt = 0
                flag = True
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

        if not attackers:
            messages.error(request, "No troops sent.")
            flag = True

        if flag:
            return redirect("rally", village_id=village.id)

        attack = Attack.objects.create(
            source=village,
            destination=target,
            end_time=timezone.now() + timedelta(seconds=calculate_travel_time(village, target, [x[0] for x in attackers])),
            type=Attack.ATTACK if action == "attack" else Attack.SUPPORT,
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

        messages.success(request, "{} has been scheduled!".format("Attack" if action == "attack" else "Support"))

        return redirect("village", village_id=village.id)

    external_villages = Village.objects.filter(all_troops__original=village)
    foreign_villages = Village.objects.filter(external_troops__village=village)

    context = {
        "village": village,
        "external": external_villages,
        "foreign": foreign_villages,
    }

    return render(request, "game/rally.html", context)


@login_required
def map_coord(request):
    world = get_object_or_404(World, id=request.session["world"])

    x = request.GET.get("x")
    y = request.GET.get("y")

    try:
        vil = Village.objects.get(x=x, y=y, world=world)
        return JsonResponse({"exists": True, "name": vil.name, "owner": vil.owner.username if vil.owner else None})
    except Village.DoesNotExist:
        return JsonResponse({"exists": False})


@login_required
def report(request, report_id=None):
    if request.method == "POST":
        request.user.reports.update(read=True)
        messages.success(request, "All reports marked as read!")
        return redirect("report")

    if report_id is not None:
        report = get_object_or_404(Report, id=report_id, owner=request.user)
        report.read = True
        report.save()
        context = {
            "report": report
        }
    else:
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1
        reports = request.user.reports.order_by("read", "-created").values("title", "created", "id", "read")
        p = Paginator(reports, 10)
        try:
            page = p.page(page)
        except InvalidPage:
            page = []
        context = {
            "reports": page
        }

    return render(request, "game/report.html", context)
