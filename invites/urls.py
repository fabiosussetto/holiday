from django.conf.urls import patterns, include, url
from invites import views

urlpatterns = patterns('invites.views',
    url(r'^login/$', 'login', name='login'),
    url(r'^password-reset/$', 'password_reset', name='password_reset'),
    url(r'^password-reset-done/$', 'password_reset_done', name='password_reset_done'),
    url(r'^password-reset-confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            'password_reset_confirm', name='password_reset_confirm'),

    url(r'^profile/edit/$', views.EditProfile.as_view(), name='edit_profile'),
    url(r'^profile/cards/$', views.AddCreditCard.as_view(), name='credit_cards'),
    url(r'^profile/remove_card/(?P<card_id>[a-zA-Z0-9_]+)/$', views.RemoveCreditCard.as_view(), name='remove_card'),
    url(r'^profile/change-password/$', views.ChangePassword.as_view(), name='change_password'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^no-association$', 'no_user_association', name='no-user-association'),
    url(r'^confirm-invitation/(?P<key>[a-f0-9]{40})$', views.ConfirmInvitation.as_view(), name='confirm'),
    url(r'^invite$', views.InviteUser.as_view(), name='invite'),
    url(r'^import-contacts/$', views.ImportContacts.as_view(), name='import_contacts'),
    url(r'^resend-invitation/(?P<pk>\d+)$', views.ResendInvitation.as_view(), name='resend_invitation'),
)