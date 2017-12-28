from datetime import timedelta

from django.utils import timezone
from django.core.cache import cache

from .models import BuildTask, Building
from .constants import get_building_upgrade_time


def process(villages):
    now = timezone.now()
    for village in villages:
        lock = cache.lock("process:village:{}".format(village.id))
        if lock.acquire(blocking=False):
            try:
                finished = village.buildqueue.filter(end_time__lte=now).order_by("end_time")
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
                for task in village.buildqueue.filter(end_time__isnull=True).order_by("start_time")[:2-existing]:
                    build_time = timedelta(seconds=get_building_upgrade_time(task.type, task.new_level - 1))
                    task.end_time = now + build_time
                    task.save()
                village._do_resource_update()
            finally:
                lock.release()
