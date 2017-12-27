from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def create_village(request):
    return render(request, "create_village.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")
