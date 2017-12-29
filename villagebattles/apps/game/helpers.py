from math import sqrt, floor, ceil

from .models import Village, Building
from .constants import get_troop_travel


def get_villages(request, user=None):
    if not user:
        user = request.user
    return Village.objects.filter(world=request.session["world"], owner=user)


def get_new_village_coords(world):
    n = Village.objects.filter(world=world).count() + 1
    x, y = square_spiral(n*2)
    return (x + 500, y + 500)


def square_spiral(n):
    if n <= 1:
        return (0, 0)
    r = int((sqrt(n - 1) - 1)/2)
    length = r*2 + 3
    d = n - (length - 2)**2
    if d <= length:
        return (floor(-floor(length/2) + d) - 1, floor(length/2))
    elif d <= length*2:
        return (floor(-floor(length/2) + (d - length)) - 1, -floor(length/2))
    elif d <= length*3-2:
        dm = d - length*2
        return (ceil(-length/2), ceil(-floor(length/2) + dm))
    else:
        dm = d - (length*3-2)
        return (floor(length/2), ceil(-floor(length/2) + dm))


def calculate_travel_time(source, destination, troops):
    dist = sqrt((destination.x - source.x)**2 + (destination.y - source.y)**2)
    slowest_unit = max([get_troop_travel(x) for x in troops])
    return dist * slowest_unit


def create_default_setup(vil):
    for t in ["HQ", "WM", "IM", "CM", "WH", "FM", "RP"]:
        Building.objects.create(
            village=vil,
            type=t,
            level=1
        )
