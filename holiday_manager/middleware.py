from django.utils import timezone

class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_anonymous():
            return
        tz = request.user.timezone
        if tz:
            timezone.activate(tz)