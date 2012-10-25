from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from holiday_manager import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^add$', views.AddHolidayRequest.as_view(), name='add-request'),
    url(r'^your_requests/(?P<kind>all|approved|archived)$', views.UserHolidayRequestList.as_view(), name='user-request-list'),
    url(r'^users/list$', views.UserList.as_view(), name='user-list'),
    url(r'^users/edit/(?P<pk>\d+)$', views.EditUser.as_view(), name='user-edit'),
    
    url(r'^requests/week$', views.HolidayRequestWeek.as_view(), name='weekly-requests'),
    
    url(r'^requests/edit/(?P<pk>\d+)$', views.EditHolidayRequest.as_view(), name='request-edit'),
    url(r'^requests/list/(?P<kind>pending|approved|rejected|archived)$', views.HolidayRequestList.as_view(), name='request-list'),
    
    url(r'^groups$', views.ListApprovalGroup.as_view(), name='group-list'),
    url(r'^groups/add$', views.CreateApprovalGroup.as_view(), name='group-add'),
    url(r'^groups/edit/(?P<pk>\d+)$', views.UpdateApprovalGroup.as_view(), name='group-edit'),
    url(r'^groups/delete/(?P<pk>\d+)$', views.DeleteApprovalGroup.as_view(), name='group-delete'),
    
    url(r'^accounts/', include('invites.urls', namespace='invites')),
    
    url(r'', include('social_auth.urls')),
)


from social_auth.backends import google
from social_auth.signals import pre_update
        
def social_extra_values(sender, user, response, details, **kwargs):
    if 'id' in response and sender == google.GoogleOAuth2Backend:
        try:
            user.google_pic_url = response['picture']
            return True
        except KeyError:
            pass

pre_update.connect(social_extra_values, sender=None)