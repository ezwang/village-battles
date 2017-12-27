from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .helpers import get_new_village_coords, get_villages
from .models import Village, World


@login_required
def create_village(request):
    if get_villages(request).count() > 0:
        return redirect("dashboard")
    world = get_object_or_404(World, id=request.session["world"])
    if request.method == "POST":
        x, y = get_new_village_coords(world)
        Village.objects.create(
            x=x,
            y=y,
            name="{}'s Village".format(request.user.username),
            owner=request.user,
            world=world
        )
        messages.success(request, "Your new village has been created!")
        return redirect("dashboard")

    return render(request, "create_village.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")
