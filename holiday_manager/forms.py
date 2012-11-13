from django import forms
from django.core.exceptions import FieldError
from holiday_manager import models
from django.forms.extras import SelectDateWidget
from django.forms.models import BaseInlineFormSet
import collections

class ProjectFormMixin(object):
    
    project = None
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(ProjectFormMixin, self).__init__(*args, **kwargs)
        if project:
            self.set_project(project)
            
    def set_project(self, project):
        self.project = project
        for name, field in self.fields.items():
            if isinstance(field, forms.models.ModelChoiceField):
                try:
                    field.queryset = field.queryset.filter(project=self.project)
                except FieldError:
                    pass
                    
    def save(self, *args, **kwargs):
        self.instance.project = self.project
        return super(ProjectFormMixin, self).save(*args, **kwargs)
        


class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'slug', 'plan_users', 'plan')
        
    def save(self, **kwargs):
        return models.Project.subscription.create(self.instance)
        
        

class AddHolidayRequestForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.HolidayRequest
        fields = ('start_date', 'end_date', 'notes')
        widgets = {
            'start_date': SelectDateWidget(),
            'end_date': SelectDateWidget()
        }
        

class ApprovalGroupForm(forms.ModelForm):
    class Meta:
        model = models.ApprovalGroup
        fields = ('name',)
        
        
class ApprovalRuleForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.ApprovalRule
        fields = ('approver', 'order')
        widgets = {
            'approver': forms.Select(attrs={'class': 'select2'}),
            'order': forms.HiddenInput(attrs={'class': 'order'})
        }
        
        
class ApprovalRulesFormset(BaseInlineFormSet):
    
    def clean(self):
        try:
            approvers = [form.cleaned_data['approver'] for form in self.forms if 'approver' in form.cleaned_data]
            occourrences = collections.Counter(approvers)
            duplicates = [item for item in occourrences if occourrences[item] > 1]
            if duplicates:
                raise forms.ValidationError("You can specify an approver just once.")
        except AttributeError:
            pass
    

class ApproveRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayApproval
        fields = ('notes',)

        
class EditProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'day_count_reset_date', 'default_timezone', 'default_days_off',
                  'google_calendar_id')
        widgets = {
            'google_calendar_id': forms.Select(),
        }
        