from .game.models import World


def world_info(request):
    if "world" in request.session:
        return {"world": World.objects.get(id=request.session["world"]).name}
    return {}
