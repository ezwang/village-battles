from .game.models import World, Village
from .game.tasks import process
from .game.helpers import get_villages
from .game.quests import get_quests


def world_info(request):
    out = {}
    if request.user.is_authenticated:
        if "world" in request.session:
            out["world"] = World.objects.get(id=request.session["world"])
            out["unread"] = request.user.reports.filter(read=False).exists()
            out["current_quests"] = get_quests(out["world"], request.user)
        if "village" in request.session:
            out["current_village"] = Village.objects.prefetch_related("buildings").get(id=request.session["village"])
    return out


def process_events(request):
    if request.user.is_authenticated and "world" in request.session:
        process(get_villages(request).prefetch_related("buildings", "buildqueue"))
    return {}
