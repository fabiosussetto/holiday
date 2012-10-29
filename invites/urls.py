from django.conf.urls import patterns, include, url
from invites.views import InviteUser

urlpatterns = patterns('invites.views',
    url(r'^login/$', 'login', name='login'),
    url(r'^logout$', 'logout', name='logout'),
    url(r'^no-association$', 'no_user_association', name='no-user-association'),
    url(r'^confirm-invitation/(?P<key>[a-f0-9]{40})$', 'confirm_invitation', name='confirm'),
    url(r'^invite$', InviteUser.as_view(), name='invite'),
)