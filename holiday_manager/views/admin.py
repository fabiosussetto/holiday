from django.views import generic
from holiday_manager import models, forms
from holiday_manager.utils import redirect_to_referer
from django.forms.models import inlineformset_factory, modelformset_factory
from invites import forms as invite_forms
from invites.models import User
from holiday_manager.views import LoginRequiredViewMixin
from holiday_manager.views.base import ProjectViewMixin
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages
from paypal.standard.forms import PayPalPaymentsForm
from holiday_manager.google_calendar import GoogleCalendarApi, calendar_choices
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import login, get_backends

# Debug views
class LoginAs(ProjectViewMixin, generic.View):

    def get(self, request, **kwargs):
        user = User.objects.get(pk=kwargs['pk'])
        backend = get_backends()[0]
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        login(request, user)
        return redirect(reverse('app:dashboard', kwargs={'project': self.curr_project.slug}))

# User management

class UserList(ProjectViewMixin, generic.ListView):
    model = User
    template_name = 'holiday_manager/user_list.html'
    main_section = 'users'
    #paginate_by = 5
    
    
class EditUser(ProjectViewMixin, generic.UpdateView):
    model = User
    form_class = invite_forms.EditUserForm
    template_name = 'edit_user.html'
    main_section = 'users'
    
    def get_success_url(self):
        return reverse('app:user_edit', kwargs={'pk': self.object.pk, 'project': self.curr_project.slug})

        
class DeleteUser(ProjectViewMixin, generic.DeleteView):
    model = User
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.warning(request, 'User "%s" deleted.' % self.object)
        return redirect_to_referer(self.request)
        
# Holiday Requests

class EditHolidayRequest(ProjectViewMixin, generic.UpdateView):
    model = models.HolidayRequest
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect_to_referer(self.request)
        
        
# Approval groups

class CreateApprovalGroup(ProjectViewMixin, generic.CreateView):
    model = models.ApprovalGroup
    object = None
    
    def get_context_data(self, **kwargs):
        context = super(CreateApprovalGroup, self).get_context_data(**kwargs)
        formset = kwargs.get('formset') or self.get_formset()
        
        # TODO: refactor this creating a ProjectFormsetMixin maybe, which sets curr project even for empty form
        empty_form = formset.empty_form
        empty_form.set_project(self.curr_project)
        context.update({
            'formset': formset,
            'empty_form': empty_form # Small hack: each time this is called in the template, the form is recreated, so we can't set the project!
        })
        return context
    
    def get(self, request, *args, **kwargs):
        form_class = forms.ApprovalGroupForm
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))
    
    def formset_kwargs(self):
        kwargs = {
            'formset': forms.ApprovalRulesFormset,
            'form': forms.ApprovalRuleForm,
            'extra': 3
        }
        return kwargs
        
    def get_formset(self):
        formset_args = self.formset_kwargs()
        RuleFormSet = inlineformset_factory(models.ApprovalGroup, models.ApprovalRule, **formset_args)
        form_data = self.request.POST if self.request.method == 'POST' else None
        formset = RuleFormSet(data=form_data, instance=self.object)
        for subform in formset.forms:
            subform.set_project(self.curr_project)
        return formset
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        form_class = forms.ApprovalGroupForm
        form = self.get_form(form_class)
        formset = self.get_formset()
        if form.is_valid() and formset.is_valid():
            form.instance.project = self.curr_project
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Changes saved successfully")
            return redirect(reverse('app:group_edit', kwargs={'project': self.curr_project.slug, 'pk': self.object.pk}))
        else:
            return self.form_invalid(form=form, formset=formset)
    
    def form_invalid(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))
    
    
class UpdateApprovalGroup(CreateApprovalGroup):
    
    def formset_kwargs(self):
        kwargs = super(UpdateApprovalGroup, self).formset_kwargs();
        kwargs.update({
            'extra': 0
        })
        return kwargs
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateApprovalGroup, self).get(request, *args, **kwargs)
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateApprovalGroup, self).post(request, *args, **kwargs)
    
    
class ListApprovalGroup(ProjectViewMixin, generic.ListView):
    model = models.ApprovalGroup
    
    
class DeleteApprovalGroup(ProjectViewMixin, generic.DeleteView):
    model = models.ApprovalGroup
    
    def get_success_url(self):
        return reverse('group_list')
        
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.get_success_url())
        
        
# Project settings

class EditProjectSettings(ProjectViewMixin, generic.UpdateView):
    model = models.Project
    form_class = forms.EditProjectSettingsForm
    template_name = 'holiday_manager/project_settings.html'
    main_section = 'settings'
    active_section = 'general'
    
    def get_form(self, form_class):
        social_user = self.request.user.social_auth.get(provider='google-oauth2')
        access_token = social_user.extra_data['access_token']
        gapi = GoogleCalendarApi(api_key=settings.GOOGLE_API_KEY, access_token=access_token, auth_user=social_user)
        calendars = gapi.list_calendars()
        form = super(EditProjectSettings, self).get_form(form_class)
        form.fields['google_calendar_id'].widget.choices = [('', "Don't use Google Calendar")] + calendar_choices(calendars)
        return form
    
    def get_success_url(self):
        return reverse('app:project_settings', kwargs={'project': self.curr_project.slug})
    
    def get_object(self, queryset=None):
        return models.Project.objects.get(pk=self.curr_project.pk)
        
        
class EditProjectClosures(ProjectViewMixin, generic.UpdateView):
    model = models.Project
    form_class = forms.EditProjectClosuresForm
    template_name = 'holiday_manager/project_closures.html'
    main_section = 'settings'
    active_section = 'closures'
    object = None
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        form = self.get_form(self.form_class)
        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Changes saved successfully")
            return redirect(reverse('app:project_closures', kwargs={'project': self.curr_project.slug}))
        else:
            return self.form_invalid(formset=formset, form=form)
            
    def form_invalid(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))
    
    def get_context_data(self, **kwargs):
        context = super(EditProjectClosures, self).get_context_data(**kwargs)
        formset = kwargs.get('formset') or self.get_formset()
        # TODO: refactor this creating a ProjectFormsetMixin maybe, which sets curr project even for empty form
        empty_form = formset.empty_form
        empty_form.set_project(self.curr_project)
        context.update({
            'formset': formset,
            'empty_form': empty_form # Small hack: each time this is called in the template, the form is recreated, so we can't set the project!
        })
        return context
    
    def formset_kwargs(self):
        kwargs = {
            #'formset': forms.ApprovalRulesFormset,
            'form': forms.ClosurePeriodForm,
            'extra': 1
        }
        return kwargs
    
    def get_formset(self):
        self.object = self.curr_project
        form_data = self.request.POST if self.request.method == 'POST' else None
        formset_args = self.formset_kwargs()
        formset_class = inlineformset_factory(models.Project, models.ClosurePeriod, **formset_args)
        formset = formset_class(data=form_data, instance=self.object)
        for subform in formset.forms:
            subform.set_project(self.curr_project)
        return formset
    
    def get_success_url(self):
        return reverse('app:project_closures', kwargs={'project': self.curr_project.slug})
    
    def get_object(self, queryset=None):
        return self.curr_project
    
    
class UpgradePlan(ProjectViewMixin, generic.TemplateView):
    template_name = 'holiday_manager/upgrade_plan.html'
    
    def get_context_data(self, **kwargs):
        paypal_dict = {
            "cmd": "_xclick-subscriptions",
            "business": "h1_1352217439_biz@gmail.com",
            "a3": self.curr_project.calculate_price(),                      # monthly price 
            "p3": 1,                           # duration of each unit (depends on unit)
            "t3": "M",                         # duration unit ("M for Month")
            "src": "1",                        # make payments recur
            "sra": "1",                        # reattempt payment on payment error
            "no_note": "1",                    # remove extra notes (optional)
            "item_name": "Holiday manager subscription",
            "notify_url": self.request.build_absolute_uri(reverse('paypal:paypal-ipn')),
            "return_url": self.request.build_absolute_uri(reverse('home')),
            "cancel_return": self.request.build_absolute_uri(reverse('home')),
            'custom': 'some custom data'
        }
        # Create the instance.
        form = PayPalPaymentsForm(initial=paypal_dict, button_type="subscribe")
        return {
            'paypal_form': form
        }