from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import urlparse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from invites import forms
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from invites.models import User
from django.core.urlresolvers import reverse
from django.views import generic
from holiday_manager.models import Project
from holiday_manager.views.base import ProjectViewMixin
from django.db import transaction
from holiday_manager.utils import redirect_to_referer

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, redirect_field_name=REDIRECT_FIELD_NAME, **kwargs):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    template_name = 'login.html'
    authentication_form = forms.AuthenticationForm
    
    curr_project = Project.objects.get(slug=kwargs['project'])
    
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]

            # Use default setting if redirect_to is empty
            #if not redirect_to:
            #    redirect_to = settings.LOGIN_REDIRECT_URL
            redirect_to = reverse('app:dashboard', kwargs={'project': curr_project.slug})

            # Heavier security check -- don't allow redirection to a different
            # host.
            #elif netloc and netloc != request.get_host():
            #    redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request, initial={'project': curr_project.slug})

    request.session.set_test_cookie()

    context = {
        'form': form,
        'curr_project': curr_project,
        redirect_field_name: redirect_to,
    }
    return render(request, template_name, context)

def logout(request, **kwargs):
    curr_project = Project.objects.get(slug=kwargs['project'])
    auth_logout(request)
    return redirect(reverse('app:invites:login', kwargs={'project': curr_project.slug}))
    
def no_user_association(request):
    return render(request, 'no_user_association.html')

def confirm_invitation(request, key=None):
    user = User.registration.activate_user(key)
    if not user:
        return redirect('/wrong_key')
    
    user = authenticate(email=user.email, skip_password=True)    
    auth_login(request, user)
    return render(request, 'user_welcome.html')
    
    
class InviteUser(ProjectViewMixin, generic.CreateView):
    model = User
    object = None
    form_class = forms.InviteUserForm
    template_name = 'user_form.html'
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            password = User.objects.make_random_password()
            self.object = User.registration.create_inactive_user(
                            form.cleaned_data['email'], password, project=self.curr_project, send_email=False)
            self.object.send_activation_email(temp_password=password)
            return redirect(reverse('app:user_edit', kwargs={'project': self.curr_project.slug, 'pk': self.object.pk}))
        else:
            return self.form_invalid(form=form)
            
            
class ResendInvitation(ProjectViewMixin, generic.CreateView):
    model = User

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        password = User.objects.make_random_password()
        self.object.set_password(password)
        self.object.save()
        self.object.send_activation_email(temp_password=password)
        return redirect_to_referer(request)