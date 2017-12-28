from .game.models import World, Village
from .game.tasks import process
from .game.helpers import get_villages


def world_info(request):
    out = {}
    if "world" in request.session:
        out["world"] = World.objects.get(id=request.session["world"])
    if "village" in request.session:
        out["current_village"] = Village.objects.get(id=request.session["village"])
    return out


def process_events(request):
    process(get_villages(request).prefetch_related("buildings", "buildqueue"))
    return {}
