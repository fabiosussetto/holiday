#from invites.models import User
from django.db import models
from holiday_manager.utils import Choices
from holiday_manager.cal import date_range

class HolidayRequest(models.Model):
    
    STATUS = Choices(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    
    author = models.ForeignKey('invites.User')
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

        
class ApprovalGroup(models.Model):
    name = models.CharField(max_length=100)
    approvers = models.ManyToManyField('invites.User', through='ApprovalRule')
    
    def __unicode__(self):
        return self.name
    
class ApprovalRule(models.Model):
    group = models.ForeignKey('ApprovalGroup')
    approver = models.ForeignKey('invites.User')
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ('order',)
