from django.utils import timezone
from datetime import timedelta

from .models import BuildTask, Building
from .constants import get_building_upgrade_time


def process(villages):
    now = timezone.now()
    for village in villages:
        finished = village.buildqueue.filter(end_time__gte=now).order_by("end_time")
        for done in finished:
            build = village.buildings.filter(type=done.type)
            if build.exists():
                build = build.first()
                build.level += 1
                build.save()
            else:
                Building.objects.create(
                    village=village,
                    type=done.type,
                    level=1
                )
            done.delete()
        existing = village.buildqueue.filter(end_time__isnull=False).count()
        for task in village.buildqueue.order_by("start_time")[:2-existing]:
            task.end_time = now + timedelta(seconds=get_building_upgrade_time(task.type, task.new_level - 1))
            task.save()
        village._do_resource_update()
