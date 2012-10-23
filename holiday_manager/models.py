from django.db import models
from django.contrib.auth.models import UserManager
from holiday_manager.utils import Choices
from social_auth.signals import socialauth_registered
from django.utils import timezone

import urllib

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import models
from django.db.models.manager import EmptyManager
from django.utils.crypto import get_random_string
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.contrib import auth
# UNUSABLE_PASSWORD is still imported here for backwards compatibility
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable, UNUSABLE_PASSWORD)
from django.contrib.auth.signals import user_logged_in
from django.contrib.contenttypes.models import ContentType


# https://bitbucket.org/ubernostrum/django-registration/src/27bccd108cdef30dc0a91ed1968be17bb1e60da4/registration/models.py?at=default

import datetime
import hashlib
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    datetime_now = datetime.datetime.now
    
SHA1_RE = re.compile('^[a-f0-9]{40}$')

class RegistrationManager(models.Manager):
    """
    Custom manager for the ``RegistrationProfile`` model.
    
    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired inactive accounts.
    
    """
    ACTIVATED = u"ALREADY_ACTIVATED"
    
    def activate_user(self, activation_key):
        """
        Validate an activation key and activate the corresponding
        ``User`` if valid.
        
        If the key is valid and has not expired, return the ``User``
        after activating.
        
        If the key is not valid or has expired, return ``False``.
        
        If the key is valid but the ``User`` is already active,
        return ``False``.
        
        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to the string constant ``RegistrationProfile.ACTIVATED``
        after successful activation.

        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                user = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not user.activation_key_expired():
                user.is_active = True
                user.activation_key = self.ACTIVATED
                user.save()
                return user
        return False
    
    def create_inactive_user(self, username, email, password, send_email=True):
        """
        Create a new, inactive ``User``, generate a
        ``RegistrationProfile`` and email its activation key to the
        ``User``, returning the new ``User``.

        By default, an activation email will be sent to the new
        user. To disable this, pass ``send_email=False``.
        
        """
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        username = new_user.username
        if isinstance(username, unicode):
            username = username.encode('utf-8')
        new_user.activation_key = hashlib.sha1(salt+username).hexdigest()
        
        new_user.save()

        if send_email:
            registration_profile.send_activation_email()

        return new_user
    create_inactive_user = transaction.commit_on_success(create_inactive_user)
        
    def delete_expired_users(self):
        """
        Remove expired instances of ``RegistrationProfile`` and their
        associated ``User``s.
        """
        for profile in self.all():
            try:
                if profile.activation_key_expired():
                    user = profile.user
                    if not user.is_active:
                        user.delete()
                        profile.delete()
            except User.DoesNotExist:
                profile.delete()

                
class User(models.Model):
    """
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=30, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'))
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('e-mail address'), blank=True)
    password = models.CharField(_('password'), max_length=128)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    is_superuser = models.BooleanField(_('superuser status'), default=False,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))
    last_login = models.DateTimeField(_('last login'), default=timezone.now)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    approval_group = models.ForeignKey('ApprovalGroup', blank=True, null=True, on_delete=models.SET_NULL)
    
    activation_key = models.CharField(max_length=40)
    
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return self.username

    def natural_key(self):
        return (self.username,)

    #def get_absolute_url(self):
    #    return "/users/%s/" % urllib.quote(smart_str(self.username))

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(None)

    def has_usable_password(self):
        return is_password_usable(self.password)

    #def get_group_permissions(self, obj=None):
    #    """
    #    Returns a list of permission strings that this user has through his/her
    #    groups. This method queries all available auth backends. If an object
    #    is passed in, only permissions matching this object are returned.
    #    """
    #    permissions = set()
    #    for backend in auth.get_backends():
    #        if hasattr(backend, "get_group_permissions"):
    #            if obj is not None:
    #                permissions.update(backend.get_group_permissions(self,
    #                                                                 obj))
    #            else:
    #                permissions.update(backend.get_group_permissions(self))
    #    return permissions
    #
    #def get_all_permissions(self, obj=None):
    #    return _user_get_all_permissions(self, obj)
    #
    #def has_perm(self, perm, obj=None):
    #    """
    #    Returns True if the user has the specified permission. This method
    #    queries all available auth backends, but returns immediately if any
    #    backend returns True. Thus, a user who has permission from a single
    #    auth backend is assumed to have permission in general. If an object is
    #    provided, permissions for this specific object are checked.
    #    """
    #
    #    # Active superusers have all permissions.
    #    if self.is_active and self.is_superuser:
    #        return True
    #
    #    # Otherwise we need to check the backends.
    #    return _user_has_perm(self, perm, obj)
    #
    #def has_perms(self, perm_list, obj=None):
    #    """
    #    Returns True if the user has each of the specified permissions. If
    #    object is passed, it checks if the user has all required perms for this
    #    object.
    #    """
    #    for perm in perm_list:
    #        if not self.has_perm(perm, obj):
    #            return False
    #    return True
    #
    #def has_module_perms(self, app_label):
    #    """
    #    Returns True if the user has any permissions in the given app label.
    #    Uses pretty much the same logic as has_perm, above.
    #    """
    #    # Active superusers have all permissions.
    #    if self.is_active and self.is_superuser:
    #        return True
    #
    #    return _user_has_module_perms(self, app_label)

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    #def get_profile(self):
    #    """
    #    Returns site-specific profile for this user. Raises
    #    SiteProfileNotAvailable if this site does not allow profiles.
    #    """
    #    if not hasattr(self, '_profile_cache'):
    #        from django.conf import settings
    #        if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
    #            raise SiteProfileNotAvailable(
    #                'You need to set AUTH_PROFILE_MODULE in your project '
    #                'settings')
    #        try:
    #            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    #        except ValueError:
    #            raise SiteProfileNotAvailable(
    #                'app_label and model_name should be separated by a dot in '
    #                'the AUTH_PROFILE_MODULE setting')
    #        try:
    #            model = models.get_model(app_label, model_name)
    #            if model is None:
    #                raise SiteProfileNotAvailable(
    #                    'Unable to load the profile model, check '
    #                    'AUTH_PROFILE_MODULE in your project settings')
    #            self._profile_cache = model._default_manager.using(
    #                               self._state.db).get(user__id__exact=self.id)
    #            self._profile_cache.user = self
    #        except (ImportError, ImproperlyConfigured):
    #            raise SiteProfileNotAvailable
    #    return self._profile_cache
        
    
    def activation_key_expired(self):
        """
        Determine whether this ``RegistrationProfile``'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.
        
        Key expiration is determined by a two-step process:
        
        1. If the user has already activated, the key will have been
           reset to the string constant ``ACTIVATED``. Re-activating
           is not permitted, and so this method returns ``True`` in
           this case.

        2. Otherwise, the date the user signed up is incremented by
           the number of days specified in the setting
           ``ACCOUNT_ACTIVATION_DAYS`` (which should be the number of
           days after signup during which a user is allowed to
           activate their account); if the result is less than or
           equal to the current date, the key has expired and this
           method returns ``True``.
        
        """
        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
               (self.user.date_joined + expiration_date <= datetime_now())
    activation_key_expired.boolean = True

    def send_activation_email(self, site):
        """
        Send an activation email to the user associated with this
        ``RegistrationProfile``.
        
        The activation email will make use of two templates:

        ``registration/activation_email_subject.txt``
            This template will be used for the subject line of the
            email. Because it is used as the subject line of an email,
            this template's output **must** be only a single line of
            text; output longer than one line will be forcibly joined
            into only a single line.

        ``registration/activation_email.txt``
            This template will be used for the body of the email.

        These templates will each receive the following context
        variables:

        ``activation_key``
            The activation key for the new account.

        ``expiration_days``
            The number of days remaining during which the account may
            be activated.

        ``site``
            An object representing the site on which the user
            registered; depending on whether ``django.contrib.sites``
            is installed, this may be an instance of either
            ``django.contrib.sites.models.Site`` (if the sites
            application is installed) or
            ``django.contrib.sites.models.RequestSite`` (if
            not). Consult the documentation for the Django sites
            framework for details regarding these objects' interfaces.

        """
        ctx_dict = {'activation_key': self.activation_key,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'site': site}
        subject = render_to_string('registration/activation_email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message = render_to_string('registration/activation_email.txt',
                                   ctx_dict)
        
        self.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)



#class CustomUser(User):
#    approval_group = models.ForeignKey('ApprovalGroup', blank=True, null=True, on_delete=models.SET_NULL)
#    
#    objects = UserManager()

class HolidayRequest(models.Model):
    
    STATUS = Choices(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    
    author = models.ForeignKey(User)
    requested_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True, editable=False)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, default=STATUS.pending, max_length=50, blank=True, editable=False)
    
    
class HolidayRequestStatus(models.Model):
    
    request = models.ForeignKey('HolidayRequest')
    changed_on = models.DateTimeField(auto_now_add=True)
    prev_status = models.CharField(choices=HolidayRequest.STATUS, max_length=50)
    new_status = models.CharField(choices=HolidayRequest.STATUS, max_length=50)
    comment = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User)
    send_notification = models.BooleanField(default=True)
    
    @classmethod
    def record_change(cls, form, holiday_request, user):
        new_change_obj = form.save(commit=False)
        new_change_obj.author = user
        new_change_obj.request = holiday_request
        new_change_obj.prev_status = holiday_request.status
        new_change_obj.save()
        holiday_request.status = new_change_obj.new_status
        holiday_request.save()
        new_change_obj.notify_author()
        return new_change_obj
    
    def notify_author(self):
        if not self.send_notification:
            return
        #settings = Settings.get()
        #email_params = {}
        #context = {}
        #if self.new_status == 'approved':
        #    email_params['subject'] = settings.email_story_approved_subject
        #    context['email_content'] = settings.email_story_approved_content
        #elif self.new_status == 'rejected':
        #    email_params['subject'] = settings.email_story_rejected_subject
        #    context['email_content'] = settings.email_story_rejected_content
        #
        #email_content_context = {
        #    'author_name': self.story.author,
        #    'story_title': self.story.title
        #}
        ##Replace placeholders in the email content custom field, using the
        ##same logic Django uses to replace vars in templates
        #context['email_content'] = SafeString(format_email(Template(context['email_content'])
        #                                                .render(Context(email_content_context))))
        #
        #email_params['html_body'] = loader.get_template('emails/story_status_notification.html').render(Context(context))
        #send_email(to_address=self.story.email, **email_params)

        
class ApprovalGroup(models.Model):
    name = models.CharField(max_length=100)
    approvers = models.ManyToManyField(User, through='ApprovalRule')
    
    def __unicode__(self):
        return self.name
    
class ApprovalRule(models.Model):
    group = models.ForeignKey('ApprovalGroup')
    approver = models.ForeignKey(User)
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ('order',)
    
    
#def new_users_handler(sender, user, response, details, **kwargs):
#    print 'XXX Response: %s' % response["picture"]
#
#        
#socialauth_registered.connect(new_users_handler, sender=None)

