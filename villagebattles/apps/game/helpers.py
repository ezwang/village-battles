from math import sqrt, floor, ceil

from .models import Village


def get_villages(request, user=None):
    if not user:
        user = request.user
    return Village.objects.filter(world=request.session["world"], owner=user)


def get_new_village_coords(world):
    n = Village.objects.filter(world=world).count() + 1
    return square_spiral(n*2)


def square_spiral(n):
    if n <= 1:
        return (0, 0)
    r = int((sqrt(n - 1) - 1)/2)
    l = r*2 + 3
    d = n - (l - 2)**2
    if d <= l:
        return (floor(-floor(l/2) + d) - 1, floor(l/2))
    elif d <= l*2:
        return (floor(-floor(l/2) + (d - l)) - 1, -floor(l/2))
    elif d <= l*3-2:
        dm = d - l*2
        return (ceil(-l/2), ceil(-floor(l/2) + dm))
    else:
        dm = d - (l*3-2)
        return (floor(l/2), ceil(-floor(l/2) + dm))
