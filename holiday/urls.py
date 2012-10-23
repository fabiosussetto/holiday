from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from holiday_manager import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^add$', views.AddHolidayRequest.as_view(), name='add-request'),
    url(r'^your_requests/(?P<kind>all|approved|archived)$', views.UserHolidayRequestList.as_view(), name='user-request-list'),
    url(r'^done/$', views.done, name='done'),
    url(r'^users/list$', views.UserList.as_view(), name='user-list'),
    url(r'^users/edit/(?P<pk>\d+)$', views.EditUser.as_view(), name='user-edit'),
    url(r'^users/invite$', views.InviteUser.as_view(), name='user-invite'),
    
    url(r'^requests/edit/(?P<pk>\d+)$', views.EditHolidayRequest.as_view(), name='request-edit'),
    url(r'^requests/list/(?P<kind>pending|approved|rejected|archived)$', views.HolidayRequestList.as_view(), name='request-list'),
    
    url(r'^groups$', views.ListApprovalGroup.as_view(), name='group-list'),
    url(r'^groups/add$', views.CreateApprovalGroup.as_view(), name='group-add'),
    url(r'^groups/edit/(?P<pk>\d+)$', views.UpdateApprovalGroup.as_view(), name='group-edit'),
    url(r'^groups/delete/(?P<pk>\d+)$', views.DeleteApprovalGroup.as_view(), name='group-delete'),
    
    url(r'', include('social_auth.urls')),
    # Examples:
    # url(r'^$', 'holiday2.views.home', name='home'),
    # url(r'^holiday2/', include('holiday2.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
