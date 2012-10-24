from django import forms
from holiday_manager import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth import authenticate, login

class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name', 'approval_group', 'is_staff',)
        
class InviteUserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('email',)

        
class AddHolidayRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayRequest
        fields = ('start_date', 'end_date', 'notes')
        

class ApprovalGroupForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalGroup
        fields = ('name',)
        
        
class ApprovalRuleForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalRule
        fields = ('approver',)
        
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

        if email and password:
            self.user_cache = authenticate(email=email,
                                           password=password)
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