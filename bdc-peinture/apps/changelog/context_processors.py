from .models import Version


def derniere_version(request):
    return {"derniere_version": Version.objects.first()}
