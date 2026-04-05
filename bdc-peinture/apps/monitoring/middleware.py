import hashlib
import traceback as tb

from django.db.models import F
from django.utils import timezone


class ErrorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            from apps.monitoring.models import ErrorReport

            error_type = type(exception).__name__
            trace = tb.format_exc()
            fingerprint = hashlib.sha256(f"{error_type}{trace}".encode()).hexdigest()

            user_email = ""
            if hasattr(request, "user") and request.user.is_authenticated:
                user_email = request.user.email

            report, created = ErrorReport.objects.get_or_create(
                fingerprint=fingerprint,
                defaults={
                    "error_type": error_type,
                    "message": str(exception),
                    "traceback": trace,
                    "url": request.build_absolute_uri(),
                    "method": request.method,
                    "user_email": user_email,
                },
            )
            if not created:
                ErrorReport.objects.filter(pk=report.pk).update(
                    count=F("count") + 1,
                    last_seen=timezone.now(),
                )
        except Exception:
            pass

        return None
