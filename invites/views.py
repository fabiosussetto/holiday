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
from holiday_manager.utils import redirect_to_referer, filter_project_contacts
from social_auth.db.django_models import UserSocialAuth
from invites.google_api import google_contacts
from django.forms.models import modelformset_factory
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import base36_to_int
from invites import tasks

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

def password_reset(request, **kwargs):
    curr_project = Project.objects.get(slug=kwargs['project'])
    password_reset_form = forms.PasswordResetForm
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
            }
            form.save(curr_project, **opts)
            return redirect(reverse('app:invites:password_reset_done', kwargs={'project': curr_project.slug}))
    else:
        form = password_reset_form()
    context = {
        'form': form,
        'curr_project': curr_project,
    }
    return render(request, 'password_reset_form.html', context)

def password_reset_done(request, template_name='password_reset_done.html', **kwargs):
    curr_project = Project.objects.get(slug=kwargs['project'])
    context = {'curr_project': curr_project}
    return render(request, template_name, context)


@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb36=None, token=None,
                           template_name='password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=forms.SetPasswordForm, **kwargs):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    assert uidb36 is not None and token is not None # checked by URLconf
    curr_project = Project.objects.get(slug=kwargs['project'])
    try:
        uid_int = base36_to_int(uidb36)
        user = User.objects.get(id=uid_int)
    except (ValueError, User.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been reset.")
                return redirect(reverse('app:invites:login', kwargs={'project': curr_project.slug}))
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'curr_project': curr_project,
        'validlink': validlink,
    }
    return render(request, template_name, context)


class InviteUser(ProjectViewMixin, generic.CreateView):
    model = User
    object = None
    form_class = forms.InviteUserForm
    template_name = 'user_form.html'
    
    def get_formset(self):
        InviteFormSet = modelformset_factory(User, form=forms.ApprovalRuleForm)
        form_data = self.request.POST if self.request.method == 'POST' else None
        formset = InviteFormSet(data=form_data, instance=self.object)
        for subform in formset.forms:
            subform.set_project(self.curr_project)
        return formset
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            new_user = form.save(self.curr_project)
            messages.success(request, "Invite sent to %s." % new_user.email)
            #return redirect_to_referer(request)
            return self.render_to_response(self.get_context_data(form=self.get_form_class()()))
        else:
            return self.form_invalid(form=form)
        
        
class ConfirmInvitation(ProjectViewMixin, generic.UpdateView):
    template_name = 'confirm_invitation.html'
    form_class = forms.ConfirmInvitationForm
    
    def get_initial(self):
        return {'key': self.kwargs['key']}
    
    def get_object(self, queryset=None):
        return User.objects.get(activation_key=self.kwargs['key'])
    
    def form_valid(self, form):
        user = form.save()
        user = authenticate(email=user.email, project=self.curr_project, skip_password=True)    
        auth_login(self.request, user)
        return redirect(reverse('app:dashboard', kwargs={'project': self.curr_project.slug}))

            
class ImportContacts(ProjectViewMixin, generic.TemplateView):

    template_name = 'import_contacts.html'
    
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = {}
        try:
            contacts = filter_project_contacts(
                            google_contacts(self.request.user), self.curr_project)
            data = {'oauthed': True, 'contacts': contacts, 'import_form': forms.ImportUserForm()}
        except (UserSocialAuth.DoesNotExist,):
            data = {'oauthed': False, 'contacts': []}
        context.update(data)
        return context
    
    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        indexes = [int(index) for index in self.request.POST.getlist('index')]
        emails = self.request.POST.getlist('email')
        first_names = self.request.POST.getlist('first_name')
        last_names = self.request.POST.getlist('last_name')
        approval_groups = self.request.POST.getlist('approval_group')
        days_off_left = self.request.POST.getlist('days_off_left')
        pics = self.request.POST.getlist('google_pic_url')
        zipped = [item for index, item in enumerate(zip(emails, first_names, last_names, approval_groups, days_off_left, pics)) if index in indexes]
        contact_data = [
            {'email': item[0], 'first_name': item[1], 'last_name': item[2],
            'approval_group_id': item[3], 'days_off_left': item[4], 'google_pic_url': item[5] or None}
            for item in zipped
        ]
        for item in contact_data:
            user = User.registration.invite(self.curr_project, **item)
            tasks.fetch_google_pic.delay(user.pk)
            
        #return redirect_to_referer(self.request)
        messages.success(request, "Invitation sent to the selected contacts.")
        return self.render_to_response(self.get_context_data())
            
            
class ResendInvitation(ProjectViewMixin, generic.CreateView):
    model = User

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        password = User.objects.make_random_password()
        self.object.set_password(password)
        self.object.save()
        self.object.send_activation_email(temp_password=password)
        messages.success(request, "Invitation resent to '%s'." % self.object.email)
        return redirect_to_referer(request)
        
        
class EditProfile(ProjectViewMixin, generic.UpdateView):
    model = User
    form_class = forms.EditProfileForm
    template_name = 'edit_profile.html'
    active_section = 'profile_data'
    
    def get_success_url(self):
        return reverse('app:invites:edit_profile', kwargs={'project': self.curr_project.slug})
    
    def get_object(self, queryset=None):
        return self.request.user
        
        
class ChangePassword(ProjectViewMixin, generic.UpdateView):
    form_class = forms.PasswordChangeForm
    template_name = 'change_password.html'
    active_section = 'change_password'

    def get_form_kwargs(self):
        kwargs = {'user': self.request.user}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
            })
        return kwargs

    def get_object(self, queryset=None):
        return self.request.user
    
    
class AddCreditCard(ProjectViewMixin, generic.TemplateView):
    template_name = 'credit_cards.html'
    active_section = 'credit_cards'
    
    def get_context_data(self, **kwargs):
        context = super(AddCreditCard, self).get_context_data(**kwargs)
        context.update({
            'cards': self.request.user.get_credit_cards()    
        })
        return context
    
    def post(self, request, *args, **kwargs):
        self.request.user.add_credit_card(request.POST['paymillToken'])
        messages.success(request, "The card has been added to your account.")
        return redirect_to_referer(request)
    
class RemoveCreditCard(ProjectViewMixin, generic.TemplateView):
    
    def post(self, request, *args, **kwargs):
        self.request.user.remove_credit_card(kwargs['card_id'])
        messages.warning(request, "The card has been removed from your account.")
        return redirect_to_referer(request)