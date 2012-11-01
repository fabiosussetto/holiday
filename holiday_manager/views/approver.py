from django.views import generic
from django.core.urlresolvers import reverse
from holiday_manager import models
from holiday_manager.views import LoginRequiredViewMixin, FilteredListView
from holiday_manager.views.base import ProjectViewMixin
import datetime
from holiday_manager.cal import days_of_week
from holiday_manager import forms
from django.shortcuts import redirect

class HolidayRequestList(ProjectViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_list.html'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'
    
        
class HolidayRequestWeek(ProjectViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_week.html'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'

    def get(self, request, *args, **kwargs):
        #self.project = models.Project.objects.get(slug=kwargs['project'])
        print HolidayRequestWeek.__mro__
        print 'HolidayRequestWeek'
        curr_year, curr_week, _ = datetime.datetime.now().isocalendar()
        self.week_num = int(self.request.GET.get('week', curr_week))
        self.week_days = list(days_of_week(curr_year, self.week_num))
        self.prev_week = (self.week_days[0] - datetime.timedelta(days=1)).isocalendar()[1]
        self.next_week = (self.week_days[-1] + datetime.timedelta(days=1)).isocalendar()[1]
        return super(HolidayRequestWeek, self).get(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super(HolidayRequestWeek, self).get_context_data(**kwargs)
        context.update({
            'week_days': self.week_days,
            'week_num': self.week_num,
            'prev_week': self.prev_week,
            'next_week': self.next_week,
            #'curr_project': self.project
        })
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestWeek, self).get_queryset()
        return queryset.date_range(self.week_days[0], self.week_days[-1])
        
        
# Holiday approvals

class HolidayApprovalList(ProjectViewMixin, generic.ListView):
    model = models.HolidayApproval
    
    def get_queryset(self):
        queryset = super(HolidayApprovalList, self).get_queryset()
        return queryset.filter(
            approver=self.request.user,
            status__in=(models.HolidayApproval.STATUS.pending, models.HolidayApproval.STATUS.waiting),
        ).order_by('order')
        
        
class ApproveRequest(ProjectViewMixin, generic.UpdateView):
    model = models.HolidayApproval
    form_class = forms.ApproveRequestForm
    
    def get_success_url(self):
        return reverse('approval_list')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.approve()
        return super(ApproveRequest, self).form_valid(form)
        
        
class RejectApprovalRequest(ProjectViewMixin, generic.UpdateView):
    model = models.HolidayApproval
    
    def get_success_url(self):
        return reverse('approval_list')
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.reject()
        return redirect(self.get_success_url())
        