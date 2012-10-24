from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, render
from django.contrib.messages.api import get_messages
from django.contrib.auth import logout
import datetime
from holiday_manager.utils import redirect_to_referer
from django.db import transaction

from django.contrib.auth import authenticate, login as auth_login

from social_auth import __version__ as version
from social_auth.utils import setting

from django.views import generic
from holiday_manager import models, forms

from django.utils.decorators import method_decorator
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from django.core.urlresolvers import reverse, reverse_lazy

def home(request):
    """Home view, displays login mechanism"""
    #if request.user.is_authenticated():
    #    return HttpResponseRedirect('done')
    #else:
    return render_to_response('holiday_manager/index.html', {'version': version},
                              RequestContext(request))

    
def no_user_association(request):
    return render(request, 'holiday_manager/no_user_association.html')

def confirm_invitation(request, key=None):
    user = models.User.registration.activate_user(key)
    if not user:
        return redirect('/wrong_key')
    
    user = authenticate(email=user.email, skip_password=True)    
    auth_login(request, user)
    return render(request, 'holiday_manager/user_welcome.html')

@login_required
def done(request):
    """Login complete view, displays user data"""
    ctx = {
        'version': version,
        'last_login': request.session.get('social_auth_last_login_backend')
    }
    return render_to_response('holiday_manager/done.html', ctx, RequestContext(request))


def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'version': version,
                                             'messages': messages},
                              RequestContext(request))

    
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import urlparse
from django.conf import settings
    
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    template_name = 'holiday_manager/login.html'
    authentication_form = forms.AuthenticationForm

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]

            # Use default setting if redirect_to is empty
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Heavier security check -- don't allow redirection to a different
            # host.
            elif netloc and netloc != request.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    context = {
        'form': form,
        redirect_field_name: redirect_to,
    }
    return render(request, template_name, context)

    
def logout_view(request):
    logout(request)
    return redirect('home')

class LoginRequiredViewMixin(object):
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredViewMixin, self).dispatch(*args, **kwargs)

    
class AddHolidayRequest(LoginRequiredViewMixin, generic.CreateView):
    model = models.HolidayRequest
    form_class = forms.AddHolidayRequestForm
    success_url = '/'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
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
    model = models.User
    template_name = 'holiday_manager/user_list.html'
    #form_class = forms.AddHolidayRequestForm
    #success_url = '/'

    #def form_valid(self, form):
    #    self.object = form.save(commit=False)
    #    self.object.author = self.request.user
    #    self.object.save()
    #    return super(AddHolidayRequest, self).form_valid(form)
    
class EditUser(generic.UpdateView):
    model = models.User
    form_class = forms.UserForm
    template_name = 'holiday_manager/user_form.html'
    
    def get_success_url(self):
        return reverse('user-edit', kwargs={'pk': self.object.pk})
    
    
class EditHolidayRequest(LoginRequiredViewMixin, generic.UpdateView):
    model = models.HolidayRequest
    
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect_to_referer(self.request)
        
        
class HolidayRequestList(LoginRequiredViewMixin, generic.ListView):
    model = models.HolidayRequest
    template_name = 'holiday_manager/admin_holidayrequest_list.html'
    kind = 'pending'

    def get(self, request, *args, **kwargs):
        self.kind = kwargs['kind']
        return super(HolidayRequestList, self).get(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super(HolidayRequestList, self).get_context_data(**kwargs)
        context.update({'kind': self.kind})
        return context
    
    def get_queryset(self):
        queryset = super(HolidayRequestList, self).get_queryset()
        if self.kind == 'pending':
            queryset = queryset.filter(status=models.HolidayRequest.STATUS.pending)
        if self.kind == 'approved':
            queryset = queryset.filter(status=models.HolidayRequest.STATUS.approved)
        elif self.kind == 'rejected':
            queryset = queryset.filter(status=models.HolidayRequest.STATUS.rejected)
        elif self.kind == 'archived':
            queryset = queryset.filter(start_date__gt=datetime.datetime.now())
        return queryset.filter(author=self.request.user)

        
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

        
class InviteUser(generic.CreateView):
    model = models.User
    object = None
    form_class = forms.InviteUserForm
    
    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            password = models.User.objects.make_random_password()
            self.object = models.User.registration.create_inactive_user(form.cleaned_data['email'], password, send_email=False)
            self.object.send_activation_email(temp_password=password)
            return redirect(reverse('user-edit', kwargs={'pk': self.object.pk}))
        else:
            return self.form_invalid(form=form)