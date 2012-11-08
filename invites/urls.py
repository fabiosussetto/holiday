from django.conf.urls import patterns, include, url
from invites import views

urlpatterns = patterns('invites.views',
    url(r'^login/$', 'login', name='login'),
    url(r'^profile/edit/$', views.EditProfile.as_view(), name='edit_profile'),
    url(r'^profile/cards/$', views.AddCreditCard.as_view(), name='credit_cards'),
    url(r'^profile/change-password/$', views.ChangePassword.as_view(), name='change_password'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^no-association$', 'no_user_association', name='no-user-association'),
    url(r'^confirm-invitation/(?P<key>[a-f0-9]{40})$', 'confirm_invitation', name='confirm'),
    url(r'^invite$', views.InviteUser.as_view(), name='invite'),
    url(r'^import-contacts/$', views.ImportContacts.as_view(), name='import_contacts'),
    url(r'^resend-invitation/(?P<pk>\d+)$', views.ResendInvitation.as_view(), name='resend_invitation'),
)