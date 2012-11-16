from django import forms
from invites import models
from invites.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth import authenticate
from holiday_manager.forms import ProjectFormMixin
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD, is_password_usable, get_hasher
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.template import loader

class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name', 'approval_group', 'is_staff',)
        

class EditUserForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name', 'approval_group', 'days_off_left',
                  'is_staff', 'is_active',)        

        
class InviteUserForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.TextInput(attrs={'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name (optional)'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name (optional)'})
        }
        
    def save(self, project, commit=True):
        new_user = super(InviteUserForm, self).save(commit=False)
        new_user = User.registration.invite(project, user=new_user, commit=False)
        if commit:
            new_user.save()
        return new_user
        
        
class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set his/her password without entering the
    old password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user
        
        
class ConfirmInvitationForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.TextInput(attrs={'readonly':'readonly'})
        }
        
    key = forms.CharField(widget=forms.HiddenInput())
    
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2
        
    def save(self):
        user = super(ConfirmInvitationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['new_password1'])
        user = User.registration.activate_user(self.cleaned_data['key'], commit=False, user=user)
        user.save()
        return user
        
        
class EditProfileForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name',)
      
        
class PasswordChangeForm(BasePasswordChangeForm):
    pass
        
    
class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    email = forms.CharField(label=_("Email"), max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    project = forms.CharField(widget=forms.HiddenInput())

    error_messages = {
        'invalid_login': _("Please enter a correct email and password. "
                           "Note that both fields are case-sensitive."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        project_slug = self.cleaned_data.get('project')

        if email and password:
            self.user_cache = authenticate(email=email,
                            password=password, project_slug=project_slug)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
    
    
class PasswordResetForm(forms.Form):
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }
    email = forms.EmailField(label=_("E-mail"), max_length=75)

    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = User.objects.filter(email__iexact=email,
                                               is_active=True)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password == UNUSABLE_PASSWORD)
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(self, project, subject_template_name='password_reset_subject.txt',
             email_template_name='password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from django.core.mail import send_mail
        for user in self.users_cache:
            c = {
                'email': user.email,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
                'project': project
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])

            
class SignupForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text = _("Enter the same password as above, for verification."))

    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name')

    #def clean_username(self):
    #    # Since User.username is unique, this check is redundant,
    #    # but it sets a nicer error message than the ORM. See #13147.
    #    username = self.cleaned_data["username"]
    #    try:
    #        User.objects.get(username=username)
    #    except User.DoesNotExist:
    #        return username
    #    raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_superuser = True
        if commit:
            user.save()
        return user