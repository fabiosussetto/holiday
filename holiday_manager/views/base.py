from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.messages.api import get_messages
import datetime
from holiday_manager.utils import redirect_to_referer
from django.db import transaction

from django.views import generic
from holiday_manager import models, forms

from django.forms.models import inlineformset_factory
from django.core.urlresolvers import reverse

from invites import forms as invite_forms
from invites.models import User

from holiday_manager.cal import days_of_week

from holiday_manager.views import LoginRequiredViewMixin, FilteredListView


def home(request):
    """Home view, displays login mechanism"""
    #if request.user.is_authenticated():
    #    return HttpResponseRedirect('done')
    #else:
    return render_to_response('holiday_manager/index.html', {},
                              RequestContext(request))

    
def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'messages': messages},
                              RequestContext(request))

    
    
class AddHolidayRequest(LoginRequiredViewMixin, generic.CreateView):
    model = models.HolidayRequest
    form_class = forms.AddHolidayRequestForm
    success_url = '/'
    initial = {
        'start_date': datetime.datetime.now().date(),
        'end_date': datetime.datetime.now().date()
    }
    
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.instance.author = self.request.user
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        request, approvals = self.object.submit()
        self.object = request
        return super(AddHolidayRequest, self).form_valid(form)
    
    
class UserHolidayRequestList(LoginRequiredViewMixin, generic.ListView):
    model = models.HolidayRequest
    kind = 'all'

    def get(self, request, *args, **kwargs):
        self.kind = kwargs['kind']
        return super(UserHolidayRequestList, self).get(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super(UserHolidayRequestList, self).get_context_data(**kwargs)
        context.update({'kind': self.kind})
        return context
    
    def get_queryset(self):
        queryset = super(UserHolidayRequestList, self).get_queryset()
        if self.kind == 'approved':
            queryset = queryset.filter(status=models.HolidayRequest.STATUS.approved)
        elif self.kind == 'archived':
            queryset = queryset.filter(start_date__gt=datetime.datetime.now())
        return queryset.filter(author=self.request.user)
        
        
class UserList(LoginRequiredViewMixin, generic.ListView):
    model = User
    template_name = 'holiday_manager/user_list.html'
    #form_class = forms.AddHolidayRequestForm
    #success_url = '/'

    #def form_valid(self, form):
    #    self.object = form.save(commit=False)
    #    self.object.author = self.request.user
    #    self.object.save()
    #    return super(AddHolidayRequest, self).form_valid(form)
    
class EditUser(generic.UpdateView):
    model = User
    form_class = invite_forms.UserForm
    template_name = 'user_form.html'
    
    def get_success_url(self):
        return reverse('user-edit', kwargs={'pk': self.object.pk})
    
    
class EditHolidayRequest(LoginRequiredViewMixin, generic.UpdateView):
    model = models.HolidayRequest
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect_to_referer(self.request)
        
        
class HolidayRequestList(LoginRequiredViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_list.html'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'
    
        
class HolidayRequestWeek(LoginRequiredViewMixin, FilteredListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_week.html'
    
    kind_values = ('pending', 'approved', 'rejected', 'archived', 'expired')
    model_kind_field = 'status'

    def get(self, request, *args, **kwargs):
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
        })
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestWeek, self).get_queryset()
        return queryset.date_range(self.week_days[0], self.week_days[-1])

        
class ChangeRequestStatus(LoginRequiredViewMixin, generic.CreateView):
    model = models.HolidayRequestStatus
    #form_class = forms.AddHolidayRequestForm
    success_url = '/'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super(ChangeRequestStatus, self).form_valid(form)
        
        
class CreateApprovalGroup(generic.CreateView):
    model = models.ApprovalGroup
    object = None
    
    def get_context_data(self, **kwargs):
        context = super(CreateApprovalGroup, self).get_context_data(**kwargs)
        context.update({'formset': self.get_formset()})
        return context
    
    def get(self, request, *args, **kwargs):
        form_class = forms.ApprovalGroupForm
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))
        
    def get_formset(self):
        RuleFormSet = inlineformset_factory(models.ApprovalGroup, models.ApprovalRule)
        form_data = self.request.POST if self.request.method == 'POST' else None
        formset = RuleFormSet(data=form_data, instance=self.object)
        return formset
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        form_class = forms.ApprovalGroupForm
        form = self.get_form(form_class)
        formset = self.get_formset()
        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(reverse('group-edit', kwargs={'pk': self.object.pk}))
        else:
            return self.form_invalid(form=form, formset=formset)
    
    def form_invalid(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))
    
    
class UpdateApprovalGroup(CreateApprovalGroup):
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateApprovalGroup, self).get(request, *args, **kwargs)
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateApprovalGroup, self).post(request, *args, **kwargs)
    
class ListApprovalGroup(generic.ListView):
    model = models.ApprovalGroup
    
    
class DeleteApprovalGroup(generic.DeleteView):
    model = models.ApprovalGroup
    
    def get_success_url(self):
        return reverse('group-list')
        
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())
        
        
class HolidayApprovalList(generic.ListView):
    model = models.HolidayApproval
    
    def get_queryset(self):
        queryset = super(HolidayApprovalList, self).get_queryset()
        return queryset.filter(
            approver=self.request.user,
            status__in=(models.HolidayApproval.STATUS.pending, models.HolidayApproval.STATUS.waiting),
        ).order_by('order')
    
    
class ApproveRequest(generic.UpdateView):
    model = models.HolidayApproval
    form_class = forms.ApproveRequestForm
    
    def get_success_url(self):
        return reverse('approvalrequest-list')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.approve()
        return super(ApproveRequest, self).form_valid(form)
        
        
class CancelRequest(generic.UpdateView):
    model = models.HolidayRequest
    #form_class = forms.ApproveRequestForm
    
    def get_success_url(self):
        return reverse('user-request-list', kwargs={'kind': 'all'})
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.author_cancel()
        return HttpResponseRedirect(self.get_success_url())
        
    