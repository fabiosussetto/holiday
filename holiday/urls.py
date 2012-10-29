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
    
    url(r'^requests/approvelist/$', views.HolidayApprovalList.as_view(), name='approvalrequest-list'),
    url(r'^requests/approve/(?P<pk>\d+)$', views.ApproveRequest.as_view(), name='approve-request'),
    
    url(r'^requests/cancel/(?P<pk>\d+)$', views.CancelRequest.as_view(), name='user-cancel-request'),
    
    url(r'^requests/week(?:/(?P<kind>%s))?$' % views.HolidayRequestWeek.url_params(), views.HolidayRequestWeek.as_view(), name='weekly-requests'),
    
    url(r'^requests/edit/(?P<pk>\d+)$', views.EditHolidayRequest.as_view(), name='request-edit'),
    url(r'^requests/list/(?P<kind>%s)$' % views.HolidayRequestList.url_params(), views.HolidayRequestList.as_view(), name='request-list'),
    
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
        from urllib2 import urlopen, HTTPError
        from django.template.defaultfilters import slugify
        from django.core.files.base import ContentFile
    
        try:
            if response['picture'] and response['picture'] != user.google_pic_url:
                user.google_pic_url = response['picture']
                pic = urlopen(user.google_pic_url)
                pic_file = ContentFile(pic.read())
                user.google_pic.save('pic_%s.jpg' % slugify(user.email), pic_file)
                #thumbnailer = get_thumbnailer(File(photo_io), # from django.core.files import File
                #    relative_name=("%s%s-picture" % (settings.USERENA_MUGSHOT_PATH,
                #                                     self.profile.user.username)))
                #thumb = thumbnailer.generate_thumbnail({'size': (200, 200)})
                return True
        except KeyError:
            pass

pre_update.connect(social_extra_values, sender=None)