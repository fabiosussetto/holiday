from django import forms
from django.core.exceptions import FieldError
from holiday_manager import models
from django.forms.extras import SelectDateWidget
from django.forms.models import BaseInlineFormSet
import collections

from datafilters.filterform import FilterForm
from datafilters.specs import DatePickFilterSpec

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
            #'start_date': forms.Cha,
            #'end_date': SelectDateWidget()
        }
        
        
#class CheckHolidayRequestForm(forms.Form):
#    start_date = forms.DateField()
#    end_date = forms.DateField()
        

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
    

class ProcessRequestForm(forms.ModelForm):
    class Meta:
        model = models.HolidayApproval
        fields = ('notes', 'status')
        widgets = {
            'status': forms.HiddenInput()
        }
        
    def save(self, commit=True):
        obj = super(ProcessRequestForm, self).save(commit=False)
        return obj
        
        
        new_status = self.cleaned_data['status']
        if new_status == models.HolidayApproval.STATUS.approved:
            obj.approve()
        elif new_status == models.HolidayApproval.STATUS.rejected:
            obj.reject()
        else:
            raise Exception("Unknow status: %s" % new_status)
        return obj

        
class EditProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('name', 'day_count_reset_date', 'default_timezone', 'default_days_off',
                  'google_calendar_id')
        widgets = {
            'google_calendar_id': forms.Select(),
        }
        
        
class EditProjectClosuresForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ('weekly_closure_days',)
    
    #week_day = forms.CharField(widget=forms.CheckboxSelectMultiple(choices=WEEKDAYS))
    #closure_week_days = forms.MultipleChoiceField(choices=DAY_CHOICES, widget=forms.SelectMultiple())
    #week_day = forms.CharField(max_length=100)
        
        
class ClosurePeriodForm(ProjectFormMixin, forms.ModelForm):
    class Meta:
        model = models.ClosurePeriod
        fields = ('start', 'end', 'name')
        
        
class RequestFilterForm(FilterForm):
    from_date = DatePickFilterSpec('start_date', label='From')
    end_date = DatePickFilterSpec('end_date', label='To')
