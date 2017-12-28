from .game.models import World, Village


def world_info(request):
    out = {}
    if "world" in request.session:
        out["world"] = World.objects.get(id=request.session["world"])
    if "village" in request.session:
        out["current_village"] = Village.objects.get(id=request.session["village"])
    return out
