from django.views import generic
from django.core.urlresolvers import reverse
from holiday_manager import models
from holiday_manager.views import LoginRequiredViewMixin, FilteredListView
from holiday_manager.views.base import ProjectViewMixin
import datetime
from holiday_manager.cal import days_of_week, date_range
from holiday_manager import forms
from django.shortcuts import redirect
import time
import itertools
from dateutil.relativedelta import relativedelta
from django.db.models import Q

class HolidayRequestList(ProjectViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_list.html'
    main_section = 'requests'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'
    
    def get_context_data(self, **kwargs):
        context = super(HolidayRequestList, self).get_context_data(**kwargs)
        context.update({
            'filterform': self.filterform
        })
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestList, self).get_queryset()
        self.filterform = forms.RequestFilterForm(self.request.GET)
        if self.filterform.is_valid():
            queryset = self.filterform.filter(queryset)

        return queryset
    
        
class HolidayRequestWeek(ProjectViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_week.html'
    main_section = 'requests'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'
    
    filter_by_date = False

    def get(self, request, *args, **kwargs):
        today = datetime.datetime.now().date()
        start = self.request.GET.get('start')
        self.filterform = forms.RequestFilterForm(self.request.GET)
        
        if self.filterform.is_empty():
            if start:
                start = datetime.datetime.fromtimestamp(int(start))
                self.start = start
                self.end = start + relativedelta(months=1)
                
                self.next = self.end + relativedelta(days=1)
                self.prev = self.start - relativedelta(months=1)
            else:
                start = today
                self.start = today - relativedelta(days=10)
                self.end = today + relativedelta(months=1)
                
                self.next = self.end + relativedelta(days=1)
                self.prev = today
        else:
            if self.filterform.is_valid():
                self.start = self.filterform.cleaned_data['from_date']
                self.end = self.filterform.cleaned_data['end_date']
                self.filter_by_date = True
                            
        self.week_days = list(date_range(self.start, self.end))
        return super(HolidayRequestWeek, self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(HolidayRequestWeek, self).get_context_data(**kwargs)
        
        # Group by author, we want one line in the calendar
        # for each author.
        groups = []
        for author, requests in itertools.groupby(context['object_list'], lambda x: x.author):
            groups.append((author, list(requests)))
            
        context['object_list'] = groups

        context.update({
            'week_days': self.week_days,
            'filter_form': self.filterform,
            'user_requests': models.HolidayRequest.objects.date_range(self.start, self.end).filter(author=self.request.user)
        })
        
        if not self.filter_by_date:
            context.update({
                'next': int(time.mktime(self.next.timetuple())),
                'prev': int(time.mktime(self.prev.timetuple())),
            })
        
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestWeek, self).get_queryset()
        return queryset.date_range(self.start, self.end).filter(~Q(author=self.request.user)).order_by('author')
        
        
# Holiday approvals

class HolidayApprovalList(ProjectViewMixin, generic.ListView):
    model = models.HolidayApproval
    main_section = 'requests'
    
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
        return reverse('app:approval_list', kwargs={'project': self.curr_project.slug})
    
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
        