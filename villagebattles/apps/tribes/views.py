from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Tribe, Member
from ..game.models import World


@login_required
def tribe_info(request, tribe_id):
    world = get_object_or_404(World, id=request.session["world"])
    tribe = get_object_or_404(Tribe, id=tribe_id, world=world)

    context = {
        "tribe": tribe
    }

    return render(request, "tribes/tribe_info.html", context)


@login_required
def tribe(request):
    world = get_object_or_404(World, id=request.session["world"])
    tribe = request.user.tribes.filter(world=world).first()

    if request.method == "POST":
        action = request.POST.get("action")
        if action in ["create", "join"]:
            name = request.POST.get("name")
            exists = Tribe.objects.filter(world=world, name=name).exists()
            if action == "create":
                if exists:
                    messages.error(request, "A tribe already exists with that name!")
                    return redirect("tribe")
                if not name:
                    messages.error(request, "Please enter a name for your tribe!")
                    return redirect("tribe")
                tribe = Tribe.objects.create(
                    name=name,
                    world=world
                )
                Member.objects.create(
                    user=request.user,
                    tribe=tribe
                )
                messages.success(request, "Your tribe has been created!")
                return redirect("tribe")
            elif action == "join":
                if not exists:
                    messages.error(request, "The tribe you are trying to join does not exist!")
                    return redirect("tribe")
                Member.objects.create(
                    user=request.user,
                    tribe=Tribe.objects.get(world=world, name=name)
                )
                messages.success(request, "You have requested to join this tribe!")
                return redirect("tribe")
        elif action == "leave":
            if not tribe:
                messages.error(request, "You are not in a tribe!")
                return redirect("tribe")
            Member.objects.get(tribe=tribe, user=request.user).delete()
            if tribe.members.count() == 0:
                tribe.delete()
            messages.success(request, "You have left your tribe!")
            return redirect("tribe")

        else:
            messages.error(request, "Invalid action!")
            return redirect("tribe")

    context = {
        "tribe": tribe
    }

    return render(request, "tribes/tribe.html", context)
