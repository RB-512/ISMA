from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import group_required

from .models import ErrorReport


@group_required("CDT")
def error_list(request):
    errors = ErrorReport.objects.all()
    paginator = Paginator(errors, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "monitoring/error_list.html", {"page_obj": page})


@group_required("CDT")
def error_detail(request, pk):
    report = get_object_or_404(ErrorReport, pk=pk)
    return render(request, "monitoring/error_detail.html", {"report": report})
