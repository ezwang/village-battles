from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, authenticate
from .forms import UserCreationForm


def index(request):
    if request.user.is_authenticated:
        return render(request, "dashboard.html")
    else:
        return render(request, "index.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
        else:
            messages.error(request, "Login failed! Is your username and password correct?")
    return redirect("index")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Your user account has been created! Check your email to continue.")
            return redirect("index")
        else:
            messages.error(request, "There were errors while trying to create your account.")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})
