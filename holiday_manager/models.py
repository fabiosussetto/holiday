from django.db import models
from holiday_manager.utils import Choices
from django.db.models import Q
from django.db import transaction

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
    
    STATUS = Choices(
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    )
    
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
        if not group:
            return self, []
        for index, approver in enumerate(group.ordered_approvers()):
            status = HolidayApproval.STATUS.waiting if index else HolidayApproval.STATUS.pending
            req = HolidayApproval.objects.create(approver=approver, request=self, order=index, status=status)
            approval_requests.append(req)
        return self, approval_requests
        
    def approve(self):
        self.status = HolidayRequest.STATUS.approved
        self.save()
    
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
    
    
class HolidayRequestStatus(models.Model):
    
    request = models.ForeignKey('HolidayRequest')
    changed_on = models.DateTimeField(auto_now_add=True)
    prev_status = models.CharField(choices=HolidayRequest.STATUS, max_length=50)
    new_status = models.CharField(choices=HolidayRequest.STATUS, max_length=50)
    comment = models.TextField(blank=True, null=True)
    author = models.ForeignKey('invites.User')
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
        
        
class HolidayApproval(models.Model):
    STATUS = Choices(
        ('waiting', 'Waiting'), ('pending', 'Pending'), ('approved', 'Approved'),
        ('rejected', 'Rejected'), ('cancelled', 'Cancelled')
    )
    
    approver = models.ForeignKey('invites.User')
    request = models.ForeignKey('HolidayRequest')
    status = models.CharField(choices=STATUS, default=STATUS.pending, max_length=100)
    notes = models.TextField(blank=True, null=True)
    changed_on = models.DateTimeField(blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)
    
    @transaction.commit_on_success
    def approve(self):
        self.status = HolidayApproval.STATUS.approved
        self.save()
        try:
            next_approval = HolidayApproval.objects.filter(
                request=self.request, status=HolidayApproval.STATUS.waiting).order_by('order').get()
            next_approval.status = HolidayApproval.STATUS.pending
            next_approval.save()
        except HolidayApproval.DoesNotExist:
            self.request.approve()
    
    def author_cancel(self):
        self.status = HolidayApproval.STATUS.cancelled
        self.save()

class ApprovalGroup(models.Model):
    name = models.CharField(max_length=100)
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
    approver = models.ForeignKey('invites.User')
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
        
