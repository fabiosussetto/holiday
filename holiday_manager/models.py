from django.db import models
from django.conf import settings
from holiday_manager.utils import Choices
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from holiday_manager.cal import PRETTY_TIMEZONE_CHOICES
import datetime
from holiday_manager.google_calendar import GoogleCalendarApi
from django.conf import settings

class ProjectManager(models.Manager):

    def create(self, instance):
        instance.trial_start = datetime.datetime.now()
        instance.price_per_user = settings.PRICE_PER_USERS_FUNC(instance.plan_users)
        instance.save()
        return instance

class Project(models.Model):

    PLANS = Choices(
        ('free', 'Free'),
    )
    
    name = models.CharField(
        max_length=30, verbose_name='Project name',
        help_text="The display name for this project."
    )
    slug = models.SlugField(max_length=30)
    created_on = models.DateTimeField(auto_now_add=True)
    
    # Billing
    plan = models.CharField(max_length=20, choices=PLANS, default='free')
    plan_users = models.SmallIntegerField(default=3)
    price_per_user = models.FloatField()
    trial_start = models.DateField(blank=True, null=True)
    
    # Settings
    default_days_off = models.SmallIntegerField(
        default=20,
        help_text="The default number of days off a user has per year."
    )
    day_count_reset_date = models.CharField(max_length=20, default='1/1') # day-month
    
    default_timezone = models.CharField(
        max_length=100, choices=PRETTY_TIMEZONE_CHOICES, default=settings.TIME_ZONE,
        help_text=(
            "By default, dates and time are displayed in this timezone. "
            "Every user can customise this setting in his/her profile."       
            )
    )
    
    google_calendar_id = models.CharField(max_length=200, blank=True, null=True)
    
    objects = models.Manager()
    subscription = ProjectManager()
    
    def __unicode__(self):
        return self.slug
        
    def calculate_price(self):
        return self.price_per_user * self.plan_users
        
    def is_in_trial(self):
        return self.plan == Project.PLANS.free and datetime.datetime.now().date() >= self.trial_start
        
    def trial_days_left(self):
        return (self.trial_expire_date() - datetime.datetime.now().date()).days
        
    def trial_expire_date(self):
        return self.trial_start + datetime.timedelta(days=settings.TRIAL_PERIOD_DAYS)
        
    def is_trial_expired(self):
        duration = settings.TRIAL_PERIOD_DAYS
        return datetime.datetime.now().date() > self.trial_expire_date()
        
    def get_admin(self):
        from invites.models import User
        return User.objects.get(is_superuser=True, project=self)
        

class HolidayRequestQuerySet(models.query.QuerySet):

    def date_range(self, start_date, end_date):
        return self.filter(
                Q(start_date__range=(start_date, end_date))
                | Q(end_date__range=(start_date, end_date))
            )

        
class HolidayRequestManager(models.Manager):

    def get_query_set(self): 
        model = models.get_model('holiday_manager', 'HolidayRequest')
        return HolidayRequestQuerySet(model)

    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)
            

class HolidayRequest(models.Model):

    class NotEnoughDaysLeft(Exception):
        pass
    
    STATUS = Choices(
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    )
    
    project = models.ForeignKey('Project')
    
    author = models.ForeignKey('invites.User')
    requested_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True, editable=False)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, default=STATUS.pending, max_length=50, blank=True, editable=False)
    
    objects = HolidayRequestManager()
    
    class Meta:
        ordering = ('requested_on',)
    
    @transaction.commit_on_success
    def submit(self):
        self.save()
        approval_requests = []
        group = self.author.approval_group
        if not group and self.author.is_superuser:
            req = HolidayApproval.objects.create(
                    approver=self.author, request=self, order=0,
                    status=HolidayApproval.STATUS.pending, project=self.project
                )
            approval_requests.append(req)
            #return self, []
        else:
            for index, approver in enumerate(group.ordered_approvers()):
                status = HolidayApproval.STATUS.waiting if index else HolidayApproval.STATUS.pending
                req = HolidayApproval.objects.create(approver=approver, request=self, order=index, status=status, project=self.project)
                approval_requests.append(req)
            
        if approval_requests:
            approval_requests[0].approver.pending_approvals += 1
            approval_requests[0].approver.save()
            
        return self, approval_requests
        
    @transaction.commit_on_success    
    def approve(self):
        self.status = HolidayRequest.STATUS.approved
        self.save()
        tot_days = (self.end_date - self.start_date).days
        if self.author.days_off_left < tot_days:
            raise HolidayRequest.NotEnoughDaysLeft()
            
        self.author.days_off_left = self.author.days_off_left - tot_days
        self.author.save()
        self.gcal_sync()
    
    @transaction.commit_on_success    
    def author_cancel(self):
        self.status = HolidayRequest.STATUS.cancelled
        self.save()
        for approval_req in self.holidayapproval_set.all():
            approval_req.author_cancel()
    
    @property        
    def is_cancellable(self):
        return self.status == HolidayRequest.STATUS.pending
        
    def clean(self):
        from django.core.exceptions import ValidationError
        same_period_requests = HolidayRequest.objects.filter(
            author=self.author,
            status__in=(HolidayRequest.STATUS.pending, HolidayRequest.STATUS.approved)
            ).date_range(self.start_date, self.end_date).count()
        if same_period_requests:
            raise ValidationError("You have already an approved or \
                pending request for the specified period.")
            
    def gcal_sync(self):
        calendar_id = self.project.google_calendar_id
        if not calendar_id:
            return
        from social_auth.db.django_models import UserSocialAuth
        
        project_admin = self.project.get_admin()
        try:
            #TODO: autorefresh token!
            access_token = project_admin.social_auth.get(provider='google-oauth2').extra_data['access_token']
        except UserSocialAuth.DoesNotExist:
            return
        
        gapi = GoogleCalendarApi(api_key=settings.GOOGLE_API_KEY, access_token=access_token)
        gapi.create_event(calendar_id,
                start=self.start_date, end=self.end_date, summary="%s holiday" % self.author)
        
    
    
class HolidayApproval(models.Model):
    STATUS = Choices(
        ('waiting', 'Waiting'), ('pending', 'Pending'), ('approved', 'Approved'),
        ('rejected', 'Rejected'), ('pre_rejected', 'Pre rejected'), ('cancelled', 'Cancelled')
    )
    
    #project = models.ForeignKey('Project')
    
    approver = models.ForeignKey('invites.User')
    request = models.ForeignKey('HolidayRequest')
    status = models.CharField(choices=STATUS, default=STATUS.pending, max_length=100)
    notes = models.TextField(blank=True, null=True)
    changed_on = models.DateTimeField(blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)
    
    project = models.ForeignKey('Project')
    
    @transaction.commit_on_success
    def approve(self):
        self.status = HolidayApproval.STATUS.approved
        self.save()
        self.approver.pending_approvals -= 1
        self.approver.save()
        try:
            next_approval = HolidayApproval.objects.filter(
                request=self.request, status=HolidayApproval.STATUS.waiting).order_by('order').get()
            
            assert(next_approval.approver_id != self.approver_id)
            next_approval.status = HolidayApproval.STATUS.pending
            next_approval.save()
            next_approval.approver.pending_approvals += 1
            next_approval.approver.save()
        except HolidayApproval.DoesNotExist:
            self.request.approve()
    
    def author_cancel(self):
        self.status = HolidayApproval.STATUS.cancelled
        self.save()
    
    @transaction.commit_on_success    
    def reject(self):
        for req in HolidayApproval.objects.filter(request_id=self.request_id, order__gt=self.order):
            req.status = HolidayApproval.STATUS.pre_rejected
            req.save()
        self.status = HolidayApproval.STATUS.rejected
        self.save()
        self.request.status = HolidayRequest.STATUS.rejected
        self.request.save()
        self.approver.pending_approvals -= 1
        self.approver.save()

        
class ApprovalGroup(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Enter the name of this group."
    )
    project = models.ForeignKey('Project')
    approvers = models.ManyToManyField('invites.User', through='ApprovalRule')
    
    def __unicode__(self):
        return self.name
        
    def ordered_approvers(self):
        approvers = []
        for rule in self.approvalrule_set.order_by('order'):
            approvers.append(rule.approver)
        return approvers

            
class ApprovalRule(models.Model):
    group = models.ForeignKey('ApprovalGroup')
    approver = models.ForeignKey('invites.User', limit_choices_to = {'is_active': True})
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ('order',)
        
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        super(ApprovalRule, self).save(*args, **kwargs)
        self.update_approver_status()
        return self
        
    @transaction.commit_on_success
    def delete(self, *args, **kwargs):
        super(ApprovalRule, self).delete(*args, **kwargs)
        self.update_approver_status()
        
    def update_approver_status(self):
        #TODO: do this only when approver changes or on create
        count = ApprovalRule.objects.filter(approver=self.approver).count()
        self.approver.is_approver = bool(count)
        self.approver.save()
        
        
#class Settings(models.Model):
#    
#    default_days_off = models.SmallIntegerField(default=20)
#    day_count_reset_date = models.CharField(max_length=20, default='01-01') # day-month


from paypal.standard.ipn.signals import subscription_signup

def on_subscription_start(sender, **kwargs):
    ipn_obj = sender
    # Undertake some action depending upon `ipn_obj`.
    print ipn_obj
    #if ipn_obj.custom == "Upgrade all users!":
        #Users.objects.update(paid=True)        
subscription_signup.connect(on_subscription_start)
    
