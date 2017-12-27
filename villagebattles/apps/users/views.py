from django.shortcuts import render, redirect
from django.contrib import messages


def index(request):
    return render(request, "index.html")


def login(request):
    if request.method == "POST":
        messages.error(request, "Login failed! Is your username and password correct?")
    return redirect("index")


def register(request):
    return render(request, "register.html")
