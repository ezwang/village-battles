from django.shortcuts import render


def index(request):
    return render(request, "index.html")


def login(request):
    if request.method == "POST":
        pass
    return redirect("index")
