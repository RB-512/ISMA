from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import Version


@login_required
def version_list(request):
    versions = Version.objects.all()
    paginator = Paginator(versions, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "changelog/version_list.html", {"page_obj": page})
