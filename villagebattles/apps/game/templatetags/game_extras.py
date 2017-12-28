from django import template
from django.utils.safestring import mark_safe

from ..constants import get_building_cost

register = template.Library()


@register.simple_tag()
def building_cost(building, level):
    wood, clay, iron = get_building_cost(building, level)
    out = []
    for res, val in [("wood", wood), ("clay", clay), ("iron", iron)]:
        out.append("<span class='" + res + "'>" + str(val) + "</span>")
    return mark_safe(" ".join(out))
