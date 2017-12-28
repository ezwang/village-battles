from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .helpers import get_new_village_coords, get_villages
from .models import Village, World, Building
from ..users.models import User


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
        for t in ["HQ", "WM", "IM", "CM"]:
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
        "villages": get_villages(request, user=user)
    }
    return render(request, "game/user_info.html", context)
