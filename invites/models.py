import datetime
import hashlib
import random
import re
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db import transaction
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable)

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from easy_thumbnails.fields import ThumbnailerImageField

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    datetime_now = datetime.datetime.now
    
from holiday_manager.models import ApprovalGroup
from django.conf import settings
from holiday_manager.cal import COMMON_TIMEZONE_CHOICES
    
SHA1_RE = re.compile('^[a-f0-9]{40}$')


class UserManager(DjangoUserManager):

    def create_user(self, email=None, password=None, project=None):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        email = UserManager.normalize_email(email)
        user = self.model(email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, date_joined=now)

        user.set_password(password)
        if project:
            user.project = project
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        u = self.create_user(email, password)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u

    def make_random_password(self, length=10,
                             allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                           'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                           '23456789'):
        """
        Generates a random password with the given length and given
        allowed_chars. Note that the default value of allowed_chars does not
        have "I" or "O" or letters and digits that look similar -- just to
        avoid confusion.
        """
        return get_random_string(length, allowed_chars)

    def get_by_natural_key(self, email):
        return self.get(email=email)

        
# https://bitbucket.org/ubernostrum/django-registration/src/27bccd108cdef30dc0a91ed1968be17bb1e60da4/registration/models.py?at=default
class RegistrationManager(models.Manager):
    """
    Custom manager for the ``RegistrationProfile`` model.
    
    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired inactive accounts.
    
    """
    ACTIVATED = u"ALREADY_ACTIVATED"
    
    def invite(self, project, email):
        password = User.objects.make_random_password()
        new_user = self.create_inactive_user(
                        email, password, project=project, send_email=False)
        new_user.send_activation_email(temp_password=password)
        return new_user
    
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
    
    def create_inactive_user(self, email, password, project=None, send_email=True):
        """
        Create a new, inactive ``User``, generate a
        ``RegistrationProfile`` and email its activation key to the
        ``User``, returning the new ``User``.

        By default, an activation email will be sent to the new
        user. To disable this, pass ``send_email=False``.
        
        """
        new_user = User.objects.create_user(email, password, project=project)
        new_user.is_active = False
        
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        new_user.activation_key = hashlib.sha1(salt + email).hexdigest()
        
        new_user.save()

        if send_email:
            new_user.send_activation_email()

        return new_user
    create_inactive_user = transaction.commit_on_success(create_inactive_user)
        
    #def delete_expired_users(self):
    #    """
    #    Remove expired instances of ``RegistrationProfile`` and their
    #    associated ``User``s.
    #    """
    #    for profile in self.all():
    #        try:
    #            if profile.activation_key_expired():
    #                user = profile.user
    #                if not user.is_active:
    #                    user.delete()
    #                    profile.delete()
    #        except User.DoesNotExist:
    #            profile.delete()

                
class User(models.Model):
    """
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    """
    #username = models.CharField(_('username'), max_length=30, unique=True,
    #    help_text=_('Required. 30 characters or fewer. Letters, numbers and '
    #                '@/./+/-/_ characters'))
    
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
    
    approval_group = models.ForeignKey(ApprovalGroup, blank=True, null=True, on_delete=models.SET_NULL)
    
    activation_key = models.CharField(max_length=40)
    
    google_pic_url = models.CharField(max_length=200, null=True, blank=True)
    
    google_pic = ThumbnailerImageField(upload_to='profiles', blank=True, null=True)
    
    is_approver = models.BooleanField(default=False)
    
    project = models.ForeignKey('holiday_manager.Project')
    
    # TODO: change the default value according to a settings model    
    days_off_left = models.SmallIntegerField(default=20)
    
    timezone = models.CharField(max_length=100, choices=COMMON_TIMEZONE_CHOICES, default=settings.TIME_ZONE)
    
    pending_approvals = models.SmallIntegerField(default=0)
    
    objects = UserManager()
    
    registration = RegistrationManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        unique_together = ('email', 'project')

    def __unicode__(self):
        if self.first_name and self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        return self.email

    def natural_key(self):
        return (self.email,)

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

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

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
        return self.activation_key == RegistrationManager.ACTIVATED or \
               (self.date_joined + expiration_date <= datetime_now())
    activation_key_expired.boolean = True

    def send_activation_email(self, temp_password=None):
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
        ctx_dict = {
            'activation_key': self.activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'temp_password': temp_password,
            'user': self
        }
        #subject = render_to_string('registration/activation_email_subject.txt',
        #                           ctx_dict)
        ## Email subject *must not* contain newlines
        #subject = ''.join(subject.splitlines())
        subject = 'Holiday - invitation'
        
        message = render_to_string('registration/activation_email.txt',
                                   ctx_dict)
        
        self.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        
