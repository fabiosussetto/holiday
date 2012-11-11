from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

def user_association_not_found(**kwargs):
    if kwargs.get('user') is None:
        return HttpResponseRedirect(reverse('app:invites:no-user-association'))
    return kwargs
    
