from datetime import timedelta

from django import template
from django.utils.safestring import mark_safe

from ..helpers import get_troop_type_display
from ..constants import (get_building_cost, get_building_population_difference, get_building_upgrade_time,
                         get_troop_cost, get_troop_population, get_troop_time, get_hq_buff, get_recruitment_buff,
                         get_troop_attack, get_troop_defense, get_troop_carry)

register = template.Library()


@register.simple_tag()
def building_cost(building, level):
    wood, clay, iron = get_building_cost(building, level)
    pop = get_building_population_difference(building, level)
    out = []
    for res, val in [("wood", wood), ("clay", clay), ("iron", iron), ("population", pop)]:
        out.append("<span class='{}'>{:,}</span>".format(res, val))
    return mark_safe(" ".join(out))


@register.simple_tag()
def troop_cost(troop):
    wood, clay, iron = get_troop_cost(troop)
    pop = get_troop_population(troop)
    out = []
    for res, val in [("wood", wood), ("clay", clay), ("iron", iron), ("population", pop)]:
        out.append("<span class='{}'>{:,}</span>".format(res, val))
    return mark_safe(" ".join(out))


@register.simple_tag()
def building_time(building, level, village):
    t = get_building_upgrade_time(building, level)
    buff = get_hq_buff(village.get_level("HQ"))
    return str(timedelta(seconds=int(t*buff)))


@register.simple_tag()
def troop_time(troop, village):
    t = get_troop_time(troop)
    buff = get_recruitment_buff("BR", village.get_level("BR"))
    return str(timedelta(seconds=int(t * buff)))


@register.simple_tag()
def troop_stats(troop, village):
    attack = get_troop_attack(troop)
    defense = get_troop_defense(troop)
    loot = get_troop_carry(troop)
    return mark_safe("<span class='attack'>{}</span><span class='defense'>{}</span><span class='resource'>{}</span>".format(attack, defense, loot))


@register.filter(name="can_build")
def can_build(village, building):
    if village.buildings.filter(type=building).exists():
        return True
    else:
        return not village.buildqueue.filter(type=building).exists()


@register.filter(name="to_hhmmss")
def to_hhmmss(time):
    return str(timedelta(seconds=int(time)))


@register.filter(name="troop_name")
def troop_name(troop):
    return get_troop_type_display(troop)
