from datetime import timedelta

from django import template
from django.utils.safestring import mark_safe

from ..constants import (get_building_cost, get_building_population_difference, get_building_upgrade_time,
                         get_troop_cost, get_troop_population, get_troop_time, get_hq_buff, get_barracks_buff)

register = template.Library()


@register.simple_tag()
def building_cost(building, level):
    wood, clay, iron = get_building_cost(building, level)
    pop = get_building_population_difference(building, level)
    out = []
    for res, val in [("wood", wood), ("clay", clay), ("iron", iron), ("population", pop)]:
        out.append("<span class='" + res + "'>" + str(val) + "</span>")
    return mark_safe(" ".join(out))


@register.simple_tag()
def troop_cost(troop):
    wood, clay, iron = get_troop_cost(troop)
    pop = get_troop_population(troop)
    out = []
    for res, val in [("wood", wood), ("clay", clay), ("iron", iron), ("population", pop)]:
        out.append("<span class='" + res + "'>" + str(val) + "</span>")
    return mark_safe(" ".join(out))


@register.simple_tag()
def building_time(building, level, village):
    t = get_building_upgrade_time(building, level)
    buff = get_hq_buff(village.get_level("HQ"))
    return str(timedelta(seconds=int(t*buff)))


@register.simple_tag()
def troop_time(troop, buff):
    t = get_troop_time(troop)
    buff = get_barracks_buff(village.get_level("BR"))
    return str(timedelta(seconds=int(t * buff)))


@register.filter(name="can_build")
def can_build(village, building):
    if village.buildings.filter(type=building).exists():
        return True
    else:
        return not village.buildqueue.filter(type=building).exists()
