from django.views import generic
from holiday_manager import models
from holiday_manager.views import LoginRequiredViewMixin
from holiday_manager.views.base import ProjectView
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from holiday_manager import forms
import datetime

        
class Dashboard(ProjectView):
    template_name = 'holiday_manager/dashboard.html'
    

    #def get(self, *args, **kwargs):
    #    return self.render_to_response()

class AddHolidayRequest(LoginRequiredViewMixin, ProjectView, generic.CreateView):
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

class UserHolidayRequestList(LoginRequiredViewMixin, ProjectView, generic.ListView):
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
        
        
class CancelRequest(ProjectView, generic.UpdateView):
    model = models.HolidayRequest
    #form_class = forms.ApproveRequestForm
    
    def get_success_url(self):
        return reverse('holiday_user_requests', kwargs={'kind': 'all'})
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.author_cancel()
        return redirect(self.get_success_url())