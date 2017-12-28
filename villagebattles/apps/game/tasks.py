from datetime import timedelta

from django.utils import timezone
from django.core.cache import cache

from .models import BuildTask, TroopTask
from .constants import get_building_upgrade_time, get_troop_time


def process(villages, now=None):
    if now is None:
        now = timezone.now()
    for village in villages:
        lock = cache.lock("process:village:{}".format(village.id))
        if lock.acquire(blocking=False):
            try:
                build_times = []
                troop_times = []

                finished = [(x.end_time, x) for x in village.buildqueue.filter(end_time__lte=now).order_by("end_time")]
                finished += [(x.end_time, x) for x in village.troopqueue.filter(end_time__lte=now).order_by("end_time")]
                finished.sort()
                for time, done in finished:
                    if isinstance(done, BuildTask):
                        build_times.append(done.end_time)
                    elif isinstance(done, TroopTask):
                        troop_times.append(done.end_time)
                    done.process()
                    done.delete()

                # Queue new buildings
                existing = village.buildqueue.filter(end_time__isnull=False).count()
                for task in village.buildqueue.filter(end_time__isnull=True).order_by("start_time")[:2-existing]:
                    build_time = timedelta(seconds=get_building_upgrade_time(task.type, task.new_level - 1))
                    task.end_time = (build_times.pop(0) if build_times else now) + build_time
                    task.save()

                # Queue new troops
                if not village.troopqueue.filter(end_time__isnull=False).exists():
                    task = village.troopqueue.filter(end_time__isnull=True).order_by("start_time").first()
                    if task:
                        build_time = timedelta(seconds=get_troop_time(task.type) * task.amount)
                        task.end_time = (troop_times.pop(0) if troop_times else now) + build_time
                        task.save()
            finally:
                lock.release()
