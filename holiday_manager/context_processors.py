from django.conf import settings

def django_settings(request):
    return {'django_settings': settings}

def ajax_partials(request):
    return {'ajax_partials': request.is_ajax() and request.GET.get('src') == 'tab' }