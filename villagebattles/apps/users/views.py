from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserCreationForm, ChangePasswordForm
from ..game.models import World
from ..game.helpers import get_villages


def index(request):
    if request.user.is_authenticated:
        num_villages = get_villages(request).count()
        if num_villages == 0:
            return redirect("create_village")
        if num_villages == 1:
            return redirect("village", village_id=get_villages(request).first().id)
        return redirect("dashboard")
    else:
        return render(request, "index.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            request.session["world"] = World.objects.all().first().id
        else:
            messages.error(request, "Login failed! Is your username and password correct?")
    return redirect("index")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            request.session["world"] = World.objects.all().first().id
            messages.success(request, "Your user account has been created! Check your email to continue.")
            return redirect("index")
        else:
            messages.error(request, "There were errors while trying to create your account.")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("index")


@login_required
def settings(request):
    form = None
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "password":
            form = ChangePasswordForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed!")
                return redirect("settings")
            else:
                messages.error(request, "Your password as not changed.")
        elif action == "profile":
            request.user.profile = request.POST.get("profile")
            request.user.save()
            messages.success(request, "Your profile has been updated!")
            return redirect("settings")
    if form is None:
        form = ChangePasswordForm(request.user)
    return render(request, "settings.html", {"password_form": form})
