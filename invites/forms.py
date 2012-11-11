from django import forms
from invites import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth import authenticate
from holiday_manager.forms import ProjectFormMixin
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm

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
        fields = ('email',)
        
        
class EditProfileForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name',)
      
        
class PasswordChangeForm(BasePasswordChangeForm):
    pass
        
class ConfirmInvitationForm(forms.Form):
    key = forms.CharField(required=True)
    email = forms.CharField(required=True)
    
    
class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    email = forms.CharField(label=_("Email"), max_length=50)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    project = forms.CharField()

    error_messages = {
        'invalid_login': _("Please enter a correct username and password. "
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