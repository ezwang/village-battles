from datetime import timedelta

from django.utils import timezone
from django.core.cache import cache

from .models import BuildTask, TroopTask
from .constants import get_building_upgrade_time, get_troop_time, get_hq_buff, get_recruitment_buff


def process(villages, now=None):
    if now is None:
        now = timezone.now()
    for village in villages:
        process_village(village, now)


def process_village(village, now):
    lock = cache.lock("process:village:{}".format(village.id))
    if lock.acquire(blocking=False):
        try:
            for other in village.outgoing.filter(end_time__lte=now):
                process_village(other.destination, now)

            while True:
                build_times = []
                troop_times = []

                finished = [(x.end_time, x) for x in village.buildqueue.filter(end_time__lte=now).order_by("end_time")]
                finished += [(x.step_time, x) for x in village.troopqueue.filter(step_time__lte=now).order_by("step_time")]
                finished += [(x.end_time, x) for x in village.incoming.filter(end_time__lte=now).order_by("end_time")]
                finished += [(x.end_time, x) for x in village.outgoing.filter(end_time__lte=now).order_by("end_time")]
                finished.sort(key=lambda x: x[0])
                for time, done in finished:
                    if isinstance(done, BuildTask):
                        build_times.append(done.end_time)
                    elif isinstance(done, TroopTask):
                        troop_times.append(done.end_time)
                    if done.process():
                        done.delete()

                processing_finished = True

                # Queue new buildings
                existing = village.buildqueue.filter(end_time__isnull=False).count()
                for task in village.buildqueue.filter(end_time__isnull=True).order_by("start_time")[:2-existing]:
                    basetime = get_building_upgrade_time(task.type, task.new_level - 1)
                    build_time = timedelta(seconds=int(basetime * get_hq_buff(village.get_level("HQ"))))
                    task.end_time = (build_times.pop(0) if build_times else now) + build_time
                    if task.end_time < now:
                        processing_finished = False
                    task.save()

                # Queue new troops
                for task in village.troopqueue.filter(end_time__isnull=True).order_by("start_time"):
                    if not task.building.troopqueue.filter(end_time__isnull=False).exists():
                        initial = (troop_times.pop(0) if troop_times else now)
                        single = int(get_troop_time(task.type) * get_recruitment_buff(task.building.type, task.building.level))
                        build_time = timedelta(seconds=single * task.amount)
                        task.end_time = initial + build_time
                        task.step_time = initial + timedelta(seconds=single)
                        if task.end_time < now:
                            processing_finished = False
                        task.save()

                if processing_finished:
                    break
        finally:
            lock.release()
