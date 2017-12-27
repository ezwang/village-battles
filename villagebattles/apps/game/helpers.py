from .models import Village


def get_villages(request, user=None):
    if not user:
        user = request.user
    return Village.objects.filter(world=request.session["world"], owner=user)
