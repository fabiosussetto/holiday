from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from holiday_manager import views

app_patterns = patterns('',
    url(r'^$', views.user.Dashboard.as_view(), name='dashboard'),
    
    url(r'^login_as/(?P<pk>\d+)/$', views.admin.LoginAs.as_view(), name='login_as'),
    
    url(r'^holiday/submit-request$', views.user.AddHolidayRequest.as_view(), name='holiday_submit'),
    url(r'^holiday/check-request$', views.user.CheckRequestAvailability.as_view(), name='check_request'),
    url(r'^holiday/request-details/$', views.approver.RequestDetails.as_view(), name='request_details'),
    
    url(r'^holiday/your-requests/(?P<kind>all|approved|archived)$', views.user.UserHolidayRequestList.as_view(), name='holiday_user_requests'),
    url(r'^holiday/(?P<pk>\d+)/cancel$', csrf_exempt(views.user.CancelRequest.as_view()), name='holiday_cancel'),
    url(r'^holiday/(?P<pk>\d+)/delete$', csrf_exempt(views.user.DeleteRequest.as_view()), name='holiday_delete'),
    
    url(r'^holiday/week(?:/(?P<kind>%s))?$' % views.approver.HolidayRequestWeek.url_params(), views.approver.HolidayRequestWeek.as_view(), name='holiday_weekly'),
    url(r'^holiday/list(?:/(?P<kind>%s))?$' % views.approver.HolidayRequestList.url_params(), views.approver.HolidayRequestList.as_view(), name='holiday_list'),
    url(r'^holiday/edit/(?P<pk>\d+)$', views.admin.EditHolidayRequest.as_view(), name='holiday_edit'),
    
    url(r'^holiday/group_ajax/(?P<pk>\d+)/$', views.approver.GroupHolidays.as_view(), name='group_ajax'),
    
    url(r'^approval/(?P<pk>\d+)/process/$', views.approver.ProcessApprovalRequest.as_view(), name='approval_process'),
    
    url(r'^approval/approvelist/$', views.approver.HolidayApprovalList.as_view(), name='approval_list'),
    #url(r'^approval/approve/(?P<pk>\d+)$', views.approver.ApproveRequest.as_view(), name='approval_approve'),
    #url(r'^approvals/approvals/reject/(?P<pk>\d+)$', views.approver.RejectApprovalRequest.as_view(), name='approval_reject'),
    
    url(r'^user/list$', views.admin.UserList.as_view(), name='user_list'),
    url(r'^user/edit/(?P<pk>\d+)$', views.admin.EditUser.as_view(), name='user_edit'),
    url(r'^user/details/(?P<pk>\d+)$', views.admin.ViewUser.as_view(), name='user_detail'),
    url(r'^user/delete/(?P<pk>\d+)$', views.admin.DeleteUser.as_view(), name='user_delete'),
    
    url(r'^project/settings/$', views.admin.EditProjectSettings.as_view(), name='project_settings'),
    url(r'^project/closures/$', views.admin.EditProjectClosures.as_view(), name='project_closures'),
    
    url(r'^group$', views.admin.ListApprovalGroup.as_view(), name='group_list'),
    url(r'^group/add$', views.admin.CreateApprovalGroup.as_view(), name='group_add'),
    url(r'^group/edit/(?P<pk>\d+)$', views.admin.UpdateApprovalGroup.as_view(), name='group_edit'),
    url(r'^group/delete/(?P<pk>\d+)$', views.admin.DeleteApprovalGroup.as_view(), name='group_delete'),
    
    url(r'^upgrade$', views.admin.UpgradePlan.as_view(), name='upgrade_plan'),
    
    url(r'^accounts/', include('invites.urls', namespace='invites')),
)

urlpatterns = patterns('',
    url(r'^$', views.public.home, name='home'),
    url(r'^subscribe/$', views.public.subscribe, name='subscribe'),
    url(r'^project/register$', views.base.CreateProject.as_view(), name='project_register'),
    (r'^app/(?P<project>[a-zA-Z0-9-]+)/', include(app_patterns, namespace='app')),
    url(r'', include('social_auth.urls')),
    url(r'^paypal_ipn/', include('paypal.standard.ipn.urls', namespace='paypal')),
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