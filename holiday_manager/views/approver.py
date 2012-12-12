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
from django.shortcuts import get_object_or_404
from django.contrib import messages

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
                            
        self.week_days = list(date_range(self.start, self.end))
        return super(HolidayRequestWeek, self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(HolidayRequestWeek, self).get_context_data(**kwargs)
        
        # Group by author, we want one line in the calendar
        # for each author.
        groups = []
        for author, requests in itertools.groupby(context['object_list'], lambda x: x.author):
            groups.append((author, list(requests)))
            
        team_groups = []
        for team, members in itertools.groupby(groups, lambda x: x[0].approval_group):
            team_groups.append((team, list(members)))
            
        context['object_list'] = team_groups
        
        other_groups = []
        if self.request.user.approval_group:
            other_groups = models.ApprovalGroup.objects.exclude(id=self.request.user.approval_group.pk)

        context.update({
            'week_days': self.week_days,
            'filter_form': self.filterform,
            'user_requests': models.HolidayRequest.objects.select_related(
                    'author__approval_group').prefetch_related('project__closureperiod_set'
                    ).date_range(
                    self.start, self.end).filter(author=self.request.user),
            'other_groups': other_groups
        })
        
        if not self.filter_by_date:
            context.update({
                'start': int(time.mktime(self.start.timetuple())),
                'end': int(time.mktime(self.end.timetuple())),
                'next': int(time.mktime(self.end.timetuple())),
                'prev': int(time.mktime(self.prev.timetuple())),
            })
        
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestWeek, self).get_queryset()
        queryset = queryset.select_related('author__approval_group').prefetch_related('project__closureperiod_set')
        if self.request.user.approval_group:
            queryset = queryset.filter(author__approval_group=self.request.user.approval_group)
        return queryset.date_range(self.start, self.end).filter(~Q(author=self.request.user)).order_by('author')
        
        
class GroupHolidays(ProjectViewMixin, generic.DetailView):
    template_name = 'holiday_manager/group_ajax.html'
    model = models.ApprovalGroup
    
    def get(self, request, *args, **kwargs):
        self.start = datetime.datetime.fromtimestamp(int(request.GET.get('start')))
        self.end = datetime.datetime.fromtimestamp(int(request.GET.get('end')))
        return super(GroupHolidays, self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(GroupHolidays, self).get_context_data(**kwargs)
        queryset = models.HolidayRequest.objects.filter(author__approval_group=self.object)
        queryset = queryset.date_range(self.start, self.end).order_by('author')
        
        groups = []
        for author, requests in itertools.groupby(queryset, lambda x: x.author):
            groups.append((author, list(requests)))
        context.update({
            'object_list': groups,
            'week_days': list(date_range(self.start, self.end))
        })
        return context
        
        
class RequestDetails(ProjectViewMixin, generic.UpdateView):
    template_name = 'holiday_manager/request_details.html'
    context_object_name = 'holiday_request'
    form_class = forms.ProcessRequestForm

    def get_object(self):
        return get_object_or_404(models.HolidayRequest, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super(RequestDetails, self).get_context_data(**kwargs)
        context.update({
            'approvals': self.object.holidayapproval_set.all(),
            'next_approval': self.object.next_pending_approval()
        })
        return context
        
    def get_success_url(self):
        # TODO: return a json response instead?
        return reverse('app:dashboard', kwargs={'project': self.curr_project.slug})
    

class ProcessApprovalRequest(ProjectViewMixin, generic.UpdateView):
    model = models.HolidayApproval
    form_class = forms.ProcessRequestForm
    success_message = False
    
    def get_success_url(self):
        # TODO: return an empty response here, no need to render anything
        return '/'
    
    def form_valid(self, form):
        self.object = form.save()
        if form.cleaned_data['status'] == models.HolidayApproval.STATUS.approved:
            messages.success(self.request, "The request has been approved.")
        else:
            messages.warning(self.request, "The request has been rejected.")
        return super(ProcessApprovalRequest, self).form_valid(form)
        
        
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
        
        
#class ApproveRequest(ProjectViewMixin, generic.UpdateView):
#    model = models.HolidayApproval
#    form_class = forms.ApproveRequestForm
#    
#    def get_success_url(self):
#        return reverse('app:approval_list', kwargs={'project': self.curr_project.slug})
#    
#    def form_valid(self, form):
#        self.object = form.save(commit=False)
#        self.object.approve()
#        return super(ApproveRequest, self).form_valid(form)
#        
#        
#class RejectApprovalRequest(ProjectViewMixin, generic.UpdateView):
#    model = models.HolidayApproval
#    
#    def get_success_url(self):
#        return reverse('approval_list')
#        
#    def post(self, request, *args, **kwargs):
#        self.object = self.get_object()
#        self.object.reject()
#        return redirect(self.get_success_url())
#        